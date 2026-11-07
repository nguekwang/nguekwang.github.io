"""The security policies every page carries, built in one place.

templates/security.html.j2 writes them into each page right after <meta charset>, and
tools/security_check.py checks every built page against them. Rules: .claude/rules/security.md
here and web-security.md in the research-aide repository.

No upgrade-insecure-requests: no source allows http:, so it adds nothing, and WebKit applies it to
http://127.0.0.1, which breaks the browser check (web-security.md in research-aide).

GitHub Pages cannot send response headers, so only what works in a <meta> element is set here.
The headers the site still lacks are listed in .claude/rules/security.md.
"""
import urllib.parse

# GoatCounter's counting script. The page loads it from here, so the policy and the page share one value.
GOATCOUNTER_SCRIPT = "https://gc.zgo.at/count.js"

# Referrer policy of pages that count visits: GoatCounter needs the page's own origin, nothing more.
MEASURED_REFERRER = "strict-origin-when-cross-origin"
# Pages that count nothing send no referrer at all.
PLAIN_REFERRER = "no-referrer"

POLICIES = ("measured", "plain", "cv")


def origin(url):
    """The scheme and host of a URL, as a Content-Security-Policy source."""
    u = urllib.parse.urlsplit(url)
    return f"{u.scheme}://{u.netloc}"


def security_policies(site, policy):
    """Return {"csp": ..., "referrer": ...} for one kind of page.

    "measured": every language page and sub-page (loads GoatCounter, whose counter is `goatcounter` in data/site.yaml).
    "plain": the language chooser at / (only its own redirect script).
    "cv": the CV HTML that headless Chrome prints to PDF (only its own stylesheet, no scripts).
    """
    if policy not in POLICIES:
        raise ValueError(f"unknown security policy {policy!r}; expected one of {POLICIES}")
    script = ["'self'"]
    img = ["'self'"]
    connect = ["'none'"]
    if policy == "measured":
        counter = origin(site["goatcounter"])
        script.append(origin(GOATCOUNTER_SCRIPT))
        img.append(counter)
        # 'self': static/lang.js fetches the other language version of the page.
        connect = ["'self'", counter]
    if policy == "cv":
        script = ["'none'"]
    directives = [
        ("default-src", ["'none'"]),
        ("style-src", ["'self'"]),
        ("script-src", script),
        ("img-src", img),
        ("connect-src", connect),
        ("form-action", ["'none'"]),
        ("base-uri", ["'none'"]),
        ("object-src", ["'none'"]),
    ]
    csp = "; ".join(" ".join([name] + sources) for name, sources in directives)
    referrer = MEASURED_REFERRER if policy == "measured" else PLAIN_REFERRER
    return {"csp": csp, "referrer": referrer}
