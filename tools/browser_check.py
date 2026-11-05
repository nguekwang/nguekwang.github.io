#!/usr/bin/env python3
"""Check the built site in the three browser engines: Chromium (Chrome, Edge), Firefox (Gecko)
and WebKit (Safari, and every browser on iPhone and iPad).

Serves the built site from a local web server, opens every page of every language at desktop
width (1280 px) and phone width (390 px, as a touch device) in each engine with Playwright, and
fails if any page:
  - scrolls sideways (the page is wider than the window),
  - has a language menu panel that, when open, sticks out of the window,
  - raises a JavaScript error, or logs a console error (this includes Content-Security-Policy
    violations, which the engines do not all report the same way).

It also writes screenshots of the top of the Japanese page and every right-to-left page:
  <out>/<engine>-<lang>-<view>.png    one engine
  <out>/compare-<lang>-<view>.png     Chromium, Firefox and WebKit side by side
and <out>/summary.md, a table of the problems found (empty when there are none).

Requests that leave the local server (GoatCounter and other third parties) get an empty answer,
so the check never counts as a visit and does not log a failed load.

Usage:
  python3 tools/browser_check.py --site _site --out browser-check [--engines chromium firefox webkit]
"""
import argparse, functools, glob, http.server, os, sys, threading

import yaml
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINES = ["chromium", "firefox", "webkit"]
VIEWS = {
    "desktop": {"viewport": {"width": 1280, "height": 800}},
    # A phone: narrow, touch, no hover. Firefox has no mobile emulation in Playwright, so
    # is_mobile is only passed to the engines that support it (see context_options()).
    "mobile": {"viewport": {"width": 390, "height": 844}, "has_touch": True, "is_mobile": True},
}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def languages():
    return load_yaml(os.path.join(ROOT, "data", "site.yaml"))["languages"]


def screenshot_langs():
    """Japanese and every right-to-left language (what .claude/rules/git-and-prs.md asks for)."""
    langs = ["ja"]
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "i18n", "*.yaml"))):
        if load_yaml(path).get("dir") == "rtl":
            langs.append(os.path.basename(path)[:-5])
    return langs


def pages(site):
    """Every HTML page in the built site, as URL paths ("/", "/ja/", "/ja/institution-names/")."""
    out = []
    for path in sorted(glob.glob(os.path.join(site, "**", "index.html"), recursive=True)):
        rel = os.path.relpath(os.path.dirname(path), site)
        out.append("/" if rel == "." else f"/{rel}/")
    return out


def serve(directory):
    """Serve `directory` on a free local port in a background thread; return its base URL."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}"


def context_options(engine, view):
    opts = dict(VIEWS[view], device_scale_factor=1)
    if engine == "firefox":
        opts.pop("is_mobile")
    return opts


# Measures, in the page, everything the check fails on. Returns a list of problem strings.
# `width` is the window width we asked for: on a phone the browser may widen its layout to fit
# content that is too wide (and zoom out), so window.innerWidth cannot be trusted for this.
MEASURE = """(width) => {
  const problems = [];
  const doc = document.documentElement;
  const wide = Math.max(doc.scrollWidth, window.innerWidth);
  if (wide > width + 1)
    problems.push(`page is ${wide}px wide in a ${width}px window (scrolls sideways or zooms out)`);
  const menu = document.querySelector('details.langmenu');
  if (menu) {
    menu.open = true;
    const r = menu.querySelector('.panel').getBoundingClientRect();
    if (r.left < -1 || r.right > width + 1)
      problems.push(`language menu panel spans ${Math.round(r.left)}..${Math.round(r.right)}px, outside the ${width}px window`);
    menu.open = false;
  }
  return problems;
}"""


def check_page(context, base, path, shot=None):
    problems = []
    page = context.new_page()
    page.route("**/*", lambda route: route.continue_()
               if route.request.url.startswith(base) else route.fulfill(status=200, body=""))
    page.on("pageerror", lambda e: problems.append(f"JavaScript error: {e}"))
    page.on("console", lambda m: m.type == "error" and problems.append(f"console error: {m.text}"))
    page.goto(base + path, wait_until="load")
    page.wait_for_timeout(200)
    if shot:
        page.screenshot(path=shot)
    problems += page.evaluate(MEASURE, page.viewport_size["width"])
    page.close()
    return problems


def compare(paths, labels, out):
    ims = [Image.open(p).convert("RGB") for p in paths]
    gap, head = 12, 22
    canvas = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) - 1),
                               max(i.height for i in ims) + head), "white")
    draw, x = ImageDraw.Draw(canvas), 0
    for im, label in zip(ims, labels):
        draw.text((x + 4, 4), label, fill="black")
        canvas.paste(im, (x, head))
        x += im.width + gap
    canvas.save(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--site", default="_site")
    ap.add_argument("--out", default="browser-check")
    ap.add_argument("--engines", nargs="+", default=ENGINES, choices=ENGINES)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    base = serve(args.site)
    shots = {f"/{lang}/" for lang in screenshot_langs()}
    all_pages = pages(args.site)
    missing = [lang for lang in languages() if f"/{lang}/" not in all_pages]
    failures = [("-", "-", f"/{lang}/", "page was not built") for lang in missing]

    with sync_playwright() as pw:
        for engine in args.engines:
            browser = getattr(pw, engine).launch()
            for view in VIEWS:
                context = browser.new_context(**context_options(engine, view))
                for path in all_pages:
                    shot = None
                    if path in shots:
                        shot = os.path.join(args.out, f"{engine}-{path.strip('/')}-{view}.png")
                    for problem in check_page(context, base, path, shot):
                        failures.append((engine, view, path, problem))
                context.close()
            browser.close()

    for path in sorted(shots):
        lang = path.strip("/")
        for view in VIEWS:
            files = [os.path.join(args.out, f"{e}-{lang}-{view}.png") for e in args.engines]
            compare(files, args.engines, os.path.join(args.out, f"compare-{lang}-{view}.png"))

    lines = [f"Checked {len(all_pages)} pages x {len(VIEWS)} widths in {', '.join(args.engines)}.", ""]
    if failures:
        lines += ["| Engine | Width | Page | Problem |", "| --- | --- | --- | --- |"]
        lines += [f"| {e} | {v} | `{p}` | {msg.replace('|', '/')} |" for e, v, p, msg in failures]
    else:
        lines.append("No problems found.")
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
