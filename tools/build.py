#!/usr/bin/env python3
"""Static site generator for this site.

All page text lives in YAML under data/:
  data/site.yaml          site-wide settings, names, language order, keyword order
  data/i18n/<code>.yaml   page text for one language
  data/talks.yaml         talks (language-independent)
  data/institutions.yaml  per institution and language: official name or our translation
  data/post_editors.yaml  native speakers who post-edited a machine-translated language
HTML structure lives in templates/. This script only joins the two.

Usage:
  python3 tools/build.py            check the data, then build the site into _site/
  python3 tools/build.py --check    check the data only
  python3 tools/build.py --no-pdf   build the site without the CV PDFs (no Chrome needed)

The check fails when any language file differs in structure from data/i18n/en.yaml
(missing or extra keys, different list lengths, empty text), so every language shows the same items.

The "last updated" footer is filled in from git: the date of the latest commit that changed the
site (SITE_PATHS), formatted for each language with Babel, linked to that commit on GitHub.

Links that leave the site (http/https URLs outside site.url) open in a new tab: write() adds
target="_blank" rel="noopener noreferrer" to them in every generated HTML file, so templates
never need to set it per link. mailto: links and links between the site's own pages are left as they are.

Each language also gets a CV as a PDF at /<lang>/<site.cv_file>, made from the same data as the page:
templates/cv.html.j2 is rendered to a temporary HTML file and printed to PDF with headless Chrome
(set CHROME to its path if it is not found on PATH). The CV shows only what the page already shows.
"""
import concurrent.futures, datetime, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse

import yaml
from babel import Locale
from babel.dates import format_skeleton
from babel.lists import format_list
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup, escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "_site")
REFERENCE = "en"
# Keys whose value may be an empty string (an empty value means "do not show").
MAY_BE_EMPTY = {"mt_notice"}
# Opening tag of an <a> element; group 1 holds its attributes.
A_TAG = re.compile(r"<a\b([^>]*)>", re.IGNORECASE)
HREF = re.compile(r"""\bhref\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
# Set by main() from site.url; links under it stay in the same tab.
SITE_URL = None
# Paths whose changes count as a site update for the "last updated" footer.
# Workflow files, CLAUDE.md and requirements.txt do not change what visitors see.
SITE_PATHS = ["data", "templates", "static", "tools"]
# Page that explains how institution names are written, at /<lang>/<NAMES_SLUG>/.
NAMES_SLUG = "institution-names"
NAME_STATUSES = {"official", "translated"}
# Browsers tried, in order, for printing the CV to PDF when CHROME is not set.
CHROME_NAMES = ["chrome-headless-shell", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
# Fields allowed for one post-editor. Anything else (such as an email address) is rejected.
POST_EDITOR_FIELDS = {"name", "url"}


def load(*parts):
    with open(os.path.join(DATA, *parts), encoding="utf-8") as f:
        return yaml.safe_load(f)


def compare(ref, other, path, errors):
    """Record every place where `other` does not have the same shape as `ref`."""
    if isinstance(ref, dict):
        if not isinstance(other, dict):
            errors.append(f"{path}: expected a mapping")
            return
        for k in ref.keys() - other.keys():
            errors.append(f"{path}.{k}: missing")
        for k in other.keys() - ref.keys():
            errors.append(f"{path}.{k}: not in {REFERENCE}.yaml")
        for k in ref.keys() & other.keys():
            compare(ref[k], other[k], f"{path}.{k}", errors)
    elif isinstance(ref, list):
        if not isinstance(other, list):
            errors.append(f"{path}: expected a list")
        elif len(ref) != len(other):
            errors.append(f"{path}: {len(other)} items, {REFERENCE}.yaml has {len(ref)}")
        else:
            for i, (a, b) in enumerate(zip(ref, other)):
                compare(a, b, f"{path}[{i}]", errors)
    elif not isinstance(other, str):
        errors.append(f"{path}: expected text")
    elif not other.strip() and path.rsplit(".", 1)[-1] not in MAY_BE_EMPTY:
        errors.append(f"{path}: empty")


def check(site, texts, institutions, post_editors):
    errors = []
    i18n_dir = os.path.join(DATA, "i18n")
    on_disk = {f[:-5] for f in os.listdir(i18n_dir) if f.endswith(".yaml")}
    for code in on_disk - set(site["languages"]):
        errors.append(f"data/i18n/{code}.yaml: not listed in data/site.yaml languages")
    for code in set(site["languages"]) - on_disk:
        errors.append(f"data/i18n/{code}.yaml: listed in data/site.yaml but the file is missing")
    ref = texts.get(REFERENCE)
    if ref is not None:
        order = site.get("keywords", [])
        if len(set(order)) != len(order):
            errors.append("data/site.yaml keywords: duplicate ids")
        if set(order) != set(ref.get("keywords", {})):
            errors.append(f"data/site.yaml keywords: ids differ from data/i18n/{REFERENCE}.yaml keywords")
        for code, t in texts.items():
            compare(ref, t, code, errors)
        if set(ref.get("institutions", {})) != set(institutions.get("order", [])):
            errors.append(f"data/institutions.yaml order: ids differ from data/i18n/{REFERENCE}.yaml institutions")
    errors += check_institutions(site, institutions)
    errors += check_post_editors(site, texts, post_editors)
    for code, t in texts.items():
        if isinstance(t.get("og_locale"), str) and not re.fullmatch(r"[a-z]{2,3}_[A-Z]{2}", t["og_locale"]):
            errors.append(f"{code}.og_locale: must look like ja_JP (Open Graph locale)")
        if isinstance(t.get("updated"), str) and t["updated"].count("{date}") != 1:
            errors.append(f"{code}.updated: must contain {{date}} exactly once")
        if isinstance(t.get("post_edited"), str) and t["post_edited"].count("{names}") != 1:
            errors.append(f"{code}.post_edited: must contain {{names}} exactly once")
    return errors


def check_post_editors(site, texts, post_editors):
    """Post-editors are listed only for machine-translated languages, with a name and an optional https URL."""
    errors = []
    if not isinstance(post_editors, dict):
        return ["data/post_editors.yaml post_editors: expected a mapping of language codes"]
    for code, people in post_editors.items():
        where = f"data/post_editors.yaml {code}"
        if code not in site["languages"]:
            errors.append(f"{where}: not a language in data/site.yaml")
            continue
        if not str((texts.get(code) or {}).get("mt_notice", "")).strip():
            errors.append(f"{where}: this language is not machine-translated (its mt_notice is empty)")
        if not isinstance(people, list) or not people:
            errors.append(f"{where}: expected a list of people")
            continue
        for i, p in enumerate(people):
            if not isinstance(p, dict):
                errors.append(f"{where}[{i}]: expected name (and url)")
                continue
            for k in p.keys() - POST_EDITOR_FIELDS:
                errors.append(f"{where}[{i}].{k}: not allowed (only {sorted(POST_EDITOR_FIELDS)}; "
                              "no contact details in this public repository)")
            if not isinstance(p.get("name"), str) or not p["name"].strip():
                errors.append(f"{where}[{i}].name: missing")
            if "url" in p and not (isinstance(p["url"], str) and p["url"].startswith("https://")):
                errors.append(f"{where}[{i}].url: must start with https://")
    return errors


def notice(code, t, people):
    """The notice at the top of a page: mt_notice, or post_edited with the post-editors' names.

    Names are joined with the language's own list separators ("A, B, and C", "A、B、C") and
    linked to the URL each person chose. Returns "" (no notice) for languages the owner wrote.
    """
    if not people:
        return t["mt_notice"]
    parts = []
    for p in people:
        name = Markup("<bdi>{}</bdi>").format(p["name"])
        parts.append(Markup('<a href="{}">{}</a>').format(p["url"], name) if p.get("url") else name)
    marks = [f"\x00{i}\x00" for i in range(len(parts))]
    joined = str(escape(format_list(marks, locale=Locale.parse(code, sep="-"))))
    for mark, part in zip(marks, parts):
        joined = joined.replace(mark, str(part))
    before, after = t["post_edited"].split("{names}")
    return escape(before) + Markup(joined) + escape(after)


def check_institutions(site, institutions):
    """Every institution needs an official/translated entry for every language."""
    errors = []
    order = institutions.get("order", [])
    entries = institutions.get("institutions", {})
    if len(set(order)) != len(order):
        errors.append("data/institutions.yaml order: duplicate ids")
    if set(order) != set(entries):
        errors.append("data/institutions.yaml: ids in order differ from ids under institutions")
    langs = set(site["languages"])
    for iid, inst in entries.items():
        names = (inst or {}).get("names") or {}
        where = f"data/institutions.yaml {iid}"
        for code in langs - names.keys():
            errors.append(f"{where}.{code}: missing")
        for code in names.keys() - langs:
            errors.append(f"{where}.{code}: not a language in data/site.yaml")
        for code, n in names.items():
            status = (n or {}).get("status")
            if status not in NAME_STATUSES:
                errors.append(f"{where}.{code}: status must be one of {sorted(NAME_STATUSES)}")
            elif status == "official" and not str(n.get("source", "")).startswith("https://"):
                errors.append(f"{where}.{code}: official needs a source URL")
            elif status == "translated" and (n.get("basis") not in names or names[n["basis"]].get("status") != "official"):
                errors.append(f"{where}.{code}: basis must be a language whose name is official")
    return errors


def last_change():
    """Return (sha, date) of the latest commit that changed SITE_PATHS, or (None, today).

    Merge commits that only bring in an already-listed change are skipped by git's history
    simplification, so the link points at the commit that holds the actual diff.
    """
    try:
        shallow = subprocess.run(["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT,
                                 capture_output=True, text=True, check=True).stdout.strip()
        if shallow == "true":
            print("warning: shallow clone, the last-updated commit may be wrong "
                  "(use fetch-depth: 0)", file=sys.stderr)
        out = subprocess.run(["git", "log", "-1", "--format=%H %cs", "--", *SITE_PATHS], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
        if len(out) == 2:
            return out[0], datetime.date.fromisoformat(out[1])
    except (OSError, subprocess.CalledProcessError):
        pass
    print("warning: no git history, the last-updated date is today and has no link", file=sys.stderr)
    return None, datetime.date.today()


def updated_text(site, code, template, date):
    """Fill {date} with the month and year in the language's own format (e.g. 2026年11月)."""
    text = format_skeleton("yMMMM", date, locale=Locale.parse(code, sep="-"))
    digits = site.get("digits", {}).get(code)
    if digits:
        text = text.translate(str.maketrans("0123456789", digits))
    return template.replace("{date}", text)


def main():
    global SITE_URL
    site = load("site.yaml")
    SITE_URL = site["url"].rstrip("/")
    texts = {}
    for code in site["languages"]:
        if os.path.exists(os.path.join(DATA, "i18n", code + ".yaml")):
            texts[code] = load("i18n", code + ".yaml")
    institutions = load("institutions.yaml") or {}
    post_editors = (load("post_editors.yaml") or {}).get("post_editors") or {}
    errors = check(site, texts, institutions, post_editors)
    if errors:
        print(f"{len(errors)} problem(s) in data/:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    print(f"data OK: {len(texts)} languages share the structure of {REFERENCE}.yaml")
    if "--check" in sys.argv[1:]:
        return

    talks = (load("talks.yaml") or {}).get("talks") or []
    langs = [{"code": c, "native": texts[c]["native"], "og_locale": texts[c]["og_locale"]}
             for c in site["languages"]]
    req = site["translation_request"]
    sha, date = last_change()
    updated_url = f"{site['repo']}/commit/{sha}" if sha else None
    env = Environment(
        loader=FileSystemLoader(os.path.join(ROOT, "templates")),
        autoescape=select_autoescape(["html.j2", "xml.j2"]),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )

    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "static"), OUT)

    page = env.get_template("page.html.j2")
    for code in site["languages"]:
        ja = code == "ja"
        t = texts[code]
        h1 = site["name"]["ja"] if ja else site["name"]["latin"]
        title = f"{h1} – {t['keywords']['typology']}"
        html = page.render(
            site=site, langs=langs, talks=talks, code=code, t=t,
            h1=h1, title=title, notice=notice(code, t, post_editors.get(code)),
            updated=updated_text(site, code, t["updated"], date), updated_url=updated_url,
            jsonld=jsonld(site, code, t, title, post_editors.get(code)),
            alt_name=site["name"]["latin"] if ja else site["name"]["ja"],
            alt_lang="en" if ja else "ja",
            thesis_title=site["thesis"]["title_ja"] if ja else site["thesis"]["title_en"],
            thesis_lang="ja" if ja else "en", names_slug=NAMES_SLUG,
            footer_name=site["name"]["ja"] if ja else site["name"]["latin_short"],
            request_mailto=f"mailto:{site['email']}?subject={urllib.parse.quote(req['subject'])}&body={urllib.parse.quote(req['body'])}",
        )
        write(os.path.join(code, "index.html"), html)

    names_page = env.get_template("names.html.j2")
    for code in site["languages"]:
        t = texts[code]
        rows = []
        for iid in institutions["order"]:
            n = institutions["institutions"][iid]["names"][code]
            row = {"name": t["institutions"][iid], "status": n["status"], "source": n.get("source")}
            if n["status"] == "translated":
                row["basis_name"] = texts[n["basis"]]["institutions"][iid]
                row["basis_lang"] = n["basis"]
            rows.append(row)
        write(os.path.join(code, NAMES_SLUG, "index.html"), names_page.render(
            site=site, langs=langs, code=code, t=t, rows=rows, slug=NAMES_SLUG,
            notice=notice(code, t, post_editors.get(code)),
            title=f"{t['names_h']} – {site['name']['ja'] if code == 'ja' else site['name']['latin']}",
            updated=updated_text(site, code, t["updated"], date), updated_url=updated_url,
            footer_name=site["name"]["ja"] if code == "ja" else site["name"]["latin_short"],
        ))

    codes = site["languages"]
    en = texts[REFERENCE]
    write("index.html", env.get_template("root.html.j2").render(
        site=site, langs=langs, title=site["name"]["latin"], description=en["desc"],
        jsonld=jsonld(site, None, en, site["name"]["latin"])))
    write("llms.txt", env.get_template("llms.txt.j2").render(
        site=site, langs=langs, t=en, keywords=[en["keywords"][k] for k in site["keywords"]]))
    write("sitemap.xml", env.get_template("sitemap.xml.j2").render(site=site, codes=codes, slug=NAMES_SLUG))
    print(f"built {len(codes)} language pages (and their {NAMES_SLUG}/ pages) into _site/")

    if "--no-pdf" in sys.argv[1:]:
        print("skipped the CV PDFs (--no-pdf); the CV links on the pages point to missing files")
        return
    cv = env.get_template("cv.html.j2")
    with tempfile.TemporaryDirectory() as tmp:
        jobs = []
        for code in codes:
            ja = code == "ja"
            t = texts[code]
            src = os.path.join(tmp, code + ".html")
            with open(src, "w", encoding="utf-8") as f:
                f.write(cv.render(
                    site=site, talks=talks, code=code, t=t,
                    h1=site["name"]["ja"] if ja else site["name"]["latin"],
                    alt_name=site["name"]["latin"] if ja else site["name"]["ja"],
                    alt_lang="en" if ja else "ja",
                    thesis_title=site["thesis"]["title_ja"] if ja else site["thesis"]["title_en"],
                    thesis_lang="ja" if ja else "en",
                    updated=updated_text(site, code, t["updated"], date),
                ))
            jobs.append((src, os.path.join(OUT, code, site["cv_file"])))
        print_pdfs(find_chrome(), jobs, tmp)
    print(f"built {len(codes)} CV PDFs (/<lang>/{site['cv_file']})")


def find_chrome():
    chrome = os.environ.get("CHROME") or next(filter(None, map(shutil.which, CHROME_NAMES)), None)
    if not chrome:
        raise SystemExit("no Chrome found for the CV PDFs: set CHROME=/path/to/chrome, "
                         "or build without them with --no-pdf")
    return chrome


def print_pdfs(chrome, jobs, tmp):
    """Print each (html, pdf) pair with headless Chrome; fail if any PDF is not written."""
    def one(i, job):
        src, dst = job
        if os.path.exists(dst):
            os.remove(dst)
        cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--no-first-run", "--disable-background-networking",
               f"--user-data-dir={os.path.join(tmp, f'profile-{i}')}",
               "--no-pdf-header-footer", "--print-to-pdf-no-header",
               f"--print-to-pdf={dst}", "file://" + src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not os.path.exists(dst) or os.path.getsize(dst) == 0:
            raise SystemExit(f"Chrome did not write {dst}:\n{r.stderr}")
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        list(pool.map(one, *zip(*enumerate(jobs))))


def jsonld(site, code, t, title, post_editors=None):
    """Structured data (schema.org JSON-LD) for one page.

    Every page describes the same Person and WebSite (same @id), so search engines and
    AI assistants can join the language versions into one entity. `code` is None for the
    root language chooser. Post-editors of the page's language are listed as `contributor`.
    """
    base = site["url"]
    name = site["name"]
    person = {
        "@type": "Person",
        "@id": f"{base}/#person",
        "name": name["latin_short"],
        "alternateName": [name["latin"], name["ja"], name["nickname"]],
        "givenName": name["given"],
        "familyName": name["family"],
        "url": f"{base}/",
        "email": f"mailto:{site['email']}",
        "description": t["desc"],
        "knowsAbout": [t["keywords"][k] for k in site["keywords"]],
        "knowsLanguage": site["knows_language"],
        "alumniOf": {
            "@type": "CollegeOrUniversity",
            "name": site["alumni_of"]["name"],
            "alternateName": site["alumni_of"]["alternate_name"],
            "url": site["alumni_of"]["url"],
        },
        "sameAs": site["same_as"],
    }
    website = {
        "@type": "WebSite",
        "@id": f"{base}/#website",
        "url": f"{base}/",
        "name": name["latin"],
        "inLanguage": site["languages"],
        "about": {"@id": f"{base}/#person"},
    }
    graph = [website, person]
    if code is not None:
        url = f"{base}/{code}/"
        graph.insert(0, {
            "@type": "ProfilePage",
            "@id": f"{url}#page",
            "url": url,
            "name": title,
            "description": t["desc"],
            "inLanguage": code,
            "isPartOf": {"@id": f"{base}/#website"},
            "mainEntity": {"@id": f"{base}/#person"},
        })
        if post_editors:
            graph[0]["contributor"] = [
                {"@type": "Person", "name": p["name"], **({"url": p["url"]} if p.get("url") else {})}
                for p in post_editors]
    data = {"@context": "https://schema.org", "@graph": graph}
    # Escape "</" so the JSON can never close the surrounding <script> element.
    return Markup(json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/"))


def is_external(href):
    """True for an http(s) URL that points outside this site."""
    if not href.lower().startswith(("http://", "https://")):
        return False
    return not (SITE_URL and (href == SITE_URL or href.startswith(SITE_URL + "/")))


def open_external_in_new_tab(html):
    """Add target="_blank" rel="noopener noreferrer" to every <a> that leaves the site."""
    def fix(m):
        attrs = m.group(1)
        href = HREF.search(attrs)
        if not href or not is_external(href.group(1)) or re.search(r"\btarget\s*=", attrs, re.IGNORECASE):
            return m.group(0)
        if re.search(r"\brel\s*=", attrs, re.IGNORECASE):
            raise SystemExit(f"external link already has rel=, set target/rel in one place: {m.group(0)}")
        return f'<a{attrs} target="_blank" rel="noopener noreferrer">'
    return A_TAG.sub(fix, html)


def write(rel, text):
    if rel.endswith(".html"):
        text = open_external_in_new_tab(text)
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
