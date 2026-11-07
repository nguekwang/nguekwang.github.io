"""Check every built page against the site's security rules.

Usage: python3 tools/security_check.py [--site _site]

Fails (exit 1) when a page:
- does not start its <head> with <meta charset>, then the Content-Security-Policy and the referrer
  policy built by tools/security_policy.py (a <meta> policy covers only what comes after it);
- carries a policy that differs from that one, or a policy that breaks the rules itself
  ('unsafe-inline', 'unsafe-eval', data:, wildcards, http: sources, or a missing required directive);
- has a <style> element, a style="" attribute, an inline event handler (onclick= and the like),
  a javascript: URL, or an inline <script> other than JSON-LD;
- loads a script from anywhere but the site itself and GoatCounter;
- has a form, frame, object, embed or <base> element;
- links to or loads anything over plain http://;
- opens a link in a new tab without rel="noopener noreferrer".

tools/build.py runs the same check on the CV HTML before printing it to PDF.
Rules: .claude/rules/security.md here, web-security.md in the research-aide repository.
"""
import html.parser, os, sys

import yaml

from security_policy import GOATCOUNTER_SCRIPT, POLICIES, security_policies

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED = {
    "default-src": ["'none'"],
    "form-action": ["'none'"],
    "base-uri": ["'none'"],
    "object-src": ["'none'"],
    "upgrade-insecure-requests": [],
}
# Directives that list where things may load from; each must be set, since default-src is 'none'.
FETCH = ("script-src", "style-src", "img-src", "connect-src")
# Browsers ignore these in a <meta> policy, so writing them there only gives a false sense of safety.
IGNORED_IN_META = ("frame-ancestors", "report-uri", "report-to", "sandbox")
BANNED_SOURCES = ("'unsafe-inline'", "'unsafe-eval'", "'unsafe-hashes'", "'wasm-unsafe-eval'", "data:", "blob:",
                  "*", "http:", "https:")
BANNED_TAGS = ("style", "form", "iframe", "frame", "frameset", "object", "embed", "base")
URL_ATTRS = ("href", "src", "action", "formaction", "poster", "data", "srcset")


def check_policy(csp):
    """Problems with a Content-Security-Policy string itself."""
    problems = []
    directives = {}
    for part in filter(None, (p.strip() for p in csp.split(";"))):
        name, *sources = part.split()
        if name in directives:
            problems.append(f"CSP sets {name} twice")
        directives[name] = sources
    for name, sources in REQUIRED.items():
        if directives.get(name) != sources:
            problems.append(f"CSP must have `{' '.join([name] + sources)}`")
    for name in FETCH:
        if name not in directives:
            problems.append(f"CSP must set {name}")
    for name in IGNORED_IN_META:
        if name in directives:
            problems.append(f"CSP in <meta> must not use {name} (browsers ignore it there)")
    for name, sources in directives.items():
        for s in sources:
            if s in BANNED_SOURCES or "*" in s or s.startswith("http:"):
                problems.append(f"CSP {name} must not allow {s}")
    return problems


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []        # (tag, attrs) of every start tag, in order
        self.inline = []      # type of each <script> without src that has content
        self._script = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        self.tags.append((tag, a))
        if tag == "script" and "src" not in a:
            self._script = a.get("type", "")

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == "script":
            self._script = None

    def handle_data(self, data):
        if self._script is not None and data.strip():
            self.inline.append(self._script)


def check_page(text, expected):
    """Problems with one page; `expected` is security_policies(site, <kind>)."""
    p = Page()
    p.feed(text)
    problems = []
    head = [(t, a) for t, a in p.tags if t not in ("html", "head")][:3]
    want = [("meta", "charset"), ("meta", "http-equiv"), ("meta", "name")]
    if [(t, k) for (t, a), (_, k) in zip(head, want) if k in a] != want or len(head) < 3:
        problems.append("the <head> must start with <meta charset>, the CSP <meta> and the referrer <meta>")
    csps = [a.get("content", "") for t, a in p.tags
            if t == "meta" and a.get("http-equiv", "").lower() == "content-security-policy"]
    if csps != [expected["csp"]]:
        problems.append(f"expected exactly one CSP <meta> with `{expected['csp']}`, found {csps}")
    refs = [a.get("content", "") for t, a in p.tags if t == "meta" and a.get("name", "").lower() == "referrer"]
    if refs != [expected["referrer"]]:
        problems.append(f"expected exactly one referrer <meta> with `{expected['referrer']}`, found {refs}")
    for t, a in p.tags:
        if t in BANNED_TAGS:
            problems.append(f"<{t}> is not allowed")
        for k, v in a.items():
            if k == "style":
                problems.append(f"style= attribute on <{t}>")
            if k.startswith("on"):
                problems.append(f"inline event handler {k}= on <{t}>")
            if k in URL_ATTRS:
                low = v.strip().lower()
                if low.startswith("javascript:"):
                    problems.append(f"javascript: URL in <{t} {k}>")
                if low.startswith("http://") or " http://" in low:
                    problems.append(f"plain http:// URL in <{t} {k}={v}>")
        if t == "script" and "src" in a:
            src = a["src"]
            if src != GOATCOUNTER_SCRIPT and (":" in src or src.startswith("//")):
                problems.append(f"script from outside the site: {src}")
        if t == "a" and a.get("target") == "_blank":
            rel = a.get("rel", "").split()
            if "noopener" not in rel or "noreferrer" not in rel:
                problems.append(f"new-tab link without rel=\"noopener noreferrer\": {a.get('href')}")
    for kind in p.inline:
        if kind != "application/ld+json":
            problems.append(f"inline <script type={kind or '(none)'}> (only JSON-LD may be inline)")
    return problems


def main():
    args = sys.argv[1:]
    site_dir = os.path.join(ROOT, args[args.index("--site") + 1]) if "--site" in args else os.path.join(ROOT, "_site")
    with open(os.path.join(ROOT, "data", "site.yaml"), encoding="utf-8") as f:
        site = yaml.safe_load(f)
    errors = []
    for kind in POLICIES:
        errors += [f"policy {kind}: {e}" for e in check_policy(security_policies(site, kind)["csp"])]
    pages = 0
    for dirpath, _, files in os.walk(site_dir):
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, site_dir)
            # The language chooser at / counts nothing; every other page counts visits with GoatCounter.
            kind = "plain" if rel == "index.html" else "measured"
            with open(path, encoding="utf-8") as f:
                errors += [f"{rel}: {e}" for e in check_page(f.read(), security_policies(site, kind))]
            pages += 1
    if not pages:
        errors.append(f"no pages found in {site_dir}; build the site first")
    if errors:
        print(f"security check failed ({len(errors)} problems):", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    print(f"security OK: {pages} pages carry the site's policies and break none of its rules")


if __name__ == "__main__":
    main()
