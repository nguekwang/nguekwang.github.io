#!/usr/bin/env python3
"""Take before/after screenshots of the built site for a pull request.

Serves two built copies of the site (normally main and the pull request) from local web servers,
opens the same pages in both with a headless Chromium (Playwright), and writes:
  <out>/before-<lang>-<view>.png    the page as built from main
  <out>/after-<lang>-<view>.png     the page as built from the pull request
  <out>/compare-<lang>-<view>.png   both side by side, before on the left
  <out>/summary.md                  a table of which pages changed

<view> is "desktop" (1280 px wide) or "mobile" (390 px wide); every shot is the full page.
Requests that leave the local server (GoatCounter and other third parties) are blocked, so taking
screenshots never counts as a visit.

Usage:
  python3 tools/screenshots.py --before BASE_SITE_DIR --after _site --out screenshots [--langs ja ar]

The default languages are ja and every right-to-left language in data/i18n/*.yaml (from its CLDR data in Babel),
which is what .claude/rules/git-and-prs.md asks for.
"""
import argparse, base64, functools, glob, http.server, os, threading

from babel import Locale
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = {"desktop": {"width": 1280, "height": 800}, "mobile": {"width": 390, "height": 844}}


def default_langs():
    langs = ["ja"]
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "i18n", "*.yaml"))):
        code = os.path.basename(path)[:-5]
        if Locale.parse(code, sep="-").character_order == "right-to-left":
            langs.append(code)
    return langs


def serve(directory):
    """Serve `directory` on a free local port in a background thread; return its base URL."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}"


def shoot(browser, base, path, view, out):
    page = browser.new_page(viewport=VIEWS[view], device_scale_factor=1)
    page.route("**/*", lambda route: route.continue_()
               if route.request.url.startswith(base) else route.abort())
    page.goto(base + path, wait_until="networkidle")
    page.screenshot(path=out, full_page=True)
    # For the changed/unchanged test, hide the footer date: it differs between any two commits.
    data = page.screenshot(full_page=True, mask=[page.locator(".updated")])
    page.close()
    return data


def side_by_side(browser, before, after, label, out):
    """Render both PNGs next to each other with a caption and save the result."""
    def img(data):
        return "data:image/png;base64," + base64.b64encode(data).decode() if data else ""
    html = f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0;font:14px sans-serif;background:#fff}} .row{{display:flex;gap:16px;padding:16px;align-items:flex-start}}
.col{{flex:1}} h2{{margin:0 0 8px;font-size:15px}} img{{width:100%;border:1px solid #888}}
p{{margin:16px 16px 0}}</style>
<p>{label}</p><div class="row">
<div class="col"><h2>Before (main)</h2>{f'<img src="{img(before)}">' if before else '<p>(page does not exist)</p>'}</div>
<div class="col"><h2>After (this pull request)</h2>{f'<img src="{img(after)}">' if after else '<p>(page does not exist)</p>'}</div>
</div>"""
    page = browser.new_page(viewport={"width": 1600, "height": 800})
    page.set_content(html, wait_until="load")
    page.screenshot(path=out, full_page=True)
    page.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--before", required=True, help="built site from main")
    ap.add_argument("--after", required=True, help="built site from the pull request")
    ap.add_argument("--out", required=True)
    ap.add_argument("--langs", nargs="*", default=None)
    args = ap.parse_args()
    langs = args.langs or default_langs()
    os.makedirs(args.out, exist_ok=True)
    sites = {"before": serve(os.path.abspath(args.before)), "after": serve(os.path.abspath(args.after))}
    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in langs:
            for view in VIEWS:
                shots, files = {}, {}
                for which, base in sites.items():
                    exists = os.path.exists(os.path.join(getattr(args, which), lang, "index.html"))
                    target = os.path.join(args.out, f"{which}-{lang}-{view}.png")
                    shots[which] = shoot(browser, base, f"/{lang}/", view, target) if exists else None
                    files[which] = open(target, "rb").read() if exists else None
                name = f"compare-{lang}-{view}.png"
                side_by_side(browser, files["before"], files["after"], f"/{lang}/ ({view})",
                             os.path.join(args.out, name))
                changed = "changed" if shots["before"] != shots["after"] else "no change"
                rows.append(f"| /{lang}/ | {view} | {changed} | {name} |")
        browser.close()
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write("| Page | View | Result | File |\n|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
