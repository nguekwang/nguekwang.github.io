#!/usr/bin/env python3
"""Generate the top page for every language. Usage: python3 tools/build.py
Each language is written to /<language code>/; the site root (/) is a language chooser."""
import html, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from content import LANGS, NEW, TALKS, KEYWORDS, UNPUB, SITE_CONF as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOAT = C["goatcounter"]
SITE = C["url"]
EMAIL = C["email"]
GITHUB = C["github"]
NAME_LATN = C["name"]["latin"]
NAME_SHORT = C["name"]["latin_short"]
NAME_JA = C["name"]["ja"]
THESIS_EN = C["thesis"]["title_en"]
THESIS_JA = C["thesis"]["title_ja"]
REQ_SUBJECT = C["translation_request"]["subject"]
REQ_BODY = C["translation_request"]["body"]
COPY_FROM = C["copyright_from"]
E = html.escape

def path_of(code):
    return f"/{code}/"

def rel(from_code, to_code):
    return "../" + to_code + "/"

def page(L):
    c = L["code"]
    N = NEW.get(c, NEW["en"])
    nl = c if c in NEW else "en"
    up = "../"
    mailto = f"mailto:{EMAIL}?subject={urllib.parse.quote(REQ_SUBJECT)}&body={urllib.parse.quote(REQ_BODY)}"
    items = "".join(
        f'<li><span lang="{o["code"]}">{E(o["native"])}</span></li>' if o["code"] == c else
        f'<li><a href="{rel(c, o["code"])}" lang="{o["code"]}" hreflang="{o["code"]}">{E(o["native"])}</a></li>'
        for o in LANGS)
    alts = "\n".join(f'<link rel="alternate" hreflang="{o["code"]}" href="{SITE}{path_of(o["code"])}">' for o in LANGS)
    if c == "ja":
        h1, alt, thesis = NAME_JA, f'<p class="alt" lang="en">{E(NAME_LATN)}</p>', THESIS_JA
    else:
        h1, alt, thesis = NAME_LATN, f'<p class="alt" lang="ja">{NAME_JA}</p>', THESIS_EN
    mt = f'<p class="mt">{E(L["mt"])}</p>' if L["mt"] else ""
    return f'''<!doctype html>
<html lang="{c}" dir="{L["dir"]}">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self' https://gc.zgo.at; img-src 'self' https://nguekwang.goatcounter.com; connect-src https://nguekwang.goatcounter.com; form-action 'none'; base-uri 'none'; object-src 'none'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(h1)}</title>
<meta name="description" content="{E(L["desc"])}">
<link rel="canonical" href="{SITE}{path_of(c)}">
{alts}
<link rel="alternate" hreflang="x-default" href="{SITE}/">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<main>
  <nav><details class="langmenu">
      <summary>{E(L["native"])}</summary>
      <div class="panel">
        <ul>{items}</ul>
        <a class="req" href="{E(mailto)}">{E(L["request"])}</a>
      </div>
    </details></nav>
  {mt}
  <header>
    <h1>{E(h1)}</h1>
    {alt}
    <p class="role">{E(L["role"])}</p>
    <p class="tagline" lang="{nl}">{E(N["tagline"])}</p>
    <p class="buttons"><a class="btn" href="mailto:{EMAIL}">{E(N["btn_email"])}</a><a class="btn ghost" href="{E(GITHUB)}">{E(N["btn_github"])}</a></p>
  </header>
  <section class="kw">
    <h2>{E(KEYWORDS[c][0])}</h2>
    <ul class="keywords">{"".join(f"<li>{E(k)}</li>" for k in KEYWORDS[c][1])}</ul>
  </section>
{talks_html(L)}

  <section lang="{nl}">
    <h2>{E(N["interests_h"])}</h2>
    <ul>{"".join(f"<li>{E(x)}</li>" for x in N["interests"])}</ul>
    <h3>{E(N["current_h"])}</h3>
    <p>{E(N["current"])}</p>
  </section>

  <section>
    <h2>{E(L["pubs_h"])}</h2>
    <p class="empty">{E(L["soon"])}</p>
  </section>

  <section lang="{nl}">
    <h2>{E(N["projects_h"])}</h2>
    <ul>{"".join(f"<li><strong>{E(a)}</strong>: {E(b)}</li>" for a, b in N["projects"])}</ul>
  </section>

  <section>
    <h2>{E(L["edu_h"])}</h2>
    <ul>
      <li>{E(L["edu"])}<br>
        <span class="meta">{E(L["thesis"])}: <bdi dir="auto" lang="{"ja" if c == "ja" else "en"}">{E(thesis)}</bdi> {E(UNPUB[c])}</span></li>
    </ul>
  </section>

  <section lang="{nl}">
    <h2>{E(N["langs_h"])}</h2>
    <p>{E(N["langs"])}</p>
  </section>

  <section>
    <h2>{E(L["contact_h"])}</h2>
    <dl class="contact">
      <dt>{E(L["email"])}</dt><dd><a href="mailto:{EMAIL}" dir="ltr">{EMAIL}</a></dd>
      <dt>GitHub</dt><dd><a href="{E(GITHUB)}" dir="ltr">github.com/nguekwang</a></dd>
    </dl>
  </section>

  <footer>{E(L["updated"])}<br><small>&copy; {COPY_FROM}– {E(NAME_JA if c == "ja" else NAME_SHORT)}</small></footer>
</main>
<script src="{up}lang.js"></script>
<script data-goatcounter="{GOAT}" async src="https://gc.zgo.at/count.js"></script>
</body>
</html>
'''

def talks_html(L):
    if not TALKS:
        return ""
    cards = "".join(f'<a class="talk"{f' href="{E(t["url"])}"' if t.get("url") else ""}><span class="meta">{E(t["date"])} / {E(t["venue"])}</span><strong>{E(t["title"])}</strong></a>' for t in TALKS)
    return f'  <section class="talks"><div class="carousel">{cards}</div></section>\n'

for L in LANGS:
    out = os.path.join(ROOT, L["code"], "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(page(L))
print(f"{len(LANGS)} pages")

# The site root (/) is a language chooser: it redirects to the version matching the browser language, keeping ?ref= and other query parameters
codes = [o["code"] for o in LANGS]
links = "".join(f'<li><a href="{o["code"]}/" lang="{o["code"]}" hreflang="{o["code"]}">{E(o["native"])}</a></li>' for o in LANGS)
alts = "\n".join(f'<link rel="alternate" hreflang="{o["code"]}" href="{SITE}/{o["code"]}/">' for o in LANGS)
with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
    f.write(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self'; connect-src 'none'; form-action 'none'; base-uri 'none'; object-src 'none'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(NAME_LATN)}</title>
<link rel="canonical" href="{SITE}/">
{alts}
<link rel="alternate" hreflang="x-default" href="{SITE}/">
<link rel="stylesheet" href="style.css">
<script src="redirect.js" data-langs="{' '.join(codes)}"></script>
</head>
<body>
<main>
  <h1>{E(NAME_LATN)}</h1>
  <p class="alt" lang="ja">{NAME_JA}</p>
  <ul class="chooser">{links}</ul>
</main>
</body>
</html>
""")
with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
    xl = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{c}" href="{SITE}/{c}/"/>' for c in codes) + f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/>'
    us = "".join(f"\n  <url>\n    <loc>{SITE}/{c}/</loc>{xl}\n  </url>" for c in codes)
    f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{us}\n</urlset>\n')
