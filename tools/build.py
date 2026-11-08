#!/usr/bin/env python3
"""Static site generator for this site.

All page text lives in YAML under data/:
  data/site.yaml          site-wide settings, names, language order, keyword groups
  data/i18n/<code>.yaml   page text for one language
  data/talks.yaml         talks (language-independent)
  data/publications.yaml  publications and theses (titles as written; labels from data/i18n)
  data/institutions.yaml  per institution and language: official name or our translation
  data/post_editors.yaml  native speakers who post-edited a machine-translated language
  data/ai_tools.yaml      services that read a project's GitHub repository, and each project's repository
HTML structure lives in templates/. This script only joins the two.

Usage:
  python3 tools/build.py            check the data, then build the site into _site/
  python3 tools/build.py --check    check the data only
  python3 tools/build.py --no-pdf   build the site without the CV PDFs (no Chrome needed)
  python3 tools/build.py --preview --out=DIR
                                    build a pull request preview into DIR: every page gets
                                    <meta name="robots" content="noindex"> so search engines skip it
                                    (.github/workflows/pages.yml publishes it under /preview/pr-<number>/)

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

from security_policy import GOATCOUNTER_SCRIPT, security_policies
from security_check import check_page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "_site")
REFERENCE = "en"
# Keys whose value may be an empty string (an empty value means "do not show").
MAY_BE_EMPTY = {"mt_notice"}
# Keys that may be only a space (Thai separates list items with a space, not a comma).
MAY_BE_SPACE = {"list_sep"}
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
# Pages of links for AI assistants, one per project with a public repository, at /<lang>/<AI_TOOLS_SLUG>/<repo name>/.
AI_TOOLS_SLUG = "ai-tools"
GITHUB_REPO = re.compile(r"[A-Za-z0-9-]+/[A-Za-z0-9._-]+")
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
        if not (other and path.rsplit(".", 1)[-1] in MAY_BE_SPACE):
            errors.append(f"{path}: empty")


def keyword_ids(site):
    """All keyword ids in display order, across the groups in data/site.yaml."""
    return [k for g in site.get("keywords", []) for k in g.get("items", [])]


def check(site, texts, institutions, post_editors, ai_tools):
    errors = []
    i18n_dir = os.path.join(DATA, "i18n")
    on_disk = {f[:-5] for f in os.listdir(i18n_dir) if f.endswith(".yaml")}
    for code in on_disk - set(site["languages"]):
        errors.append(f"data/i18n/{code}.yaml: not listed in data/site.yaml languages")
    for code in set(site["languages"]) - on_disk:
        errors.append(f"data/i18n/{code}.yaml: listed in data/site.yaml but the file is missing")
    ref = texts.get(REFERENCE)
    if ref is not None:
        groups = site.get("keywords", [])
        group_ids = [g.get("group") for g in groups]
        order = keyword_ids(site)
        if len(set(group_ids)) != len(group_ids):
            errors.append("data/site.yaml keywords: duplicate group ids")
        if set(group_ids) != set(ref.get("keyword_groups", {})):
            errors.append(f"data/site.yaml keywords: group ids differ from data/i18n/{REFERENCE}.yaml keyword_groups")
        if any(not g.get("items") for g in groups):
            errors.append("data/site.yaml keywords: every group needs at least one keyword")
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
    if ref is not None:
        errors += check_ai_tools(texts, ref, ai_tools)
    for code, t in texts.items():
        if isinstance(t.get("og_locale"), str) and not re.fullmatch(r"[a-z]{2,3}_[A-Z]{2}", t["og_locale"]):
            errors.append(f"{code}.og_locale: must look like ja_JP (Open Graph locale)")
        if isinstance(t.get("updated"), str) and t["updated"].count("{date}") != 1:
            errors.append(f"{code}.updated: must contain {{date}} exactly once")
        for key, marks in (("pub_title_en", ("{title}",)), ("pub_note", ("{year}", "{details}"))):
            for mark in marks:
                if isinstance(t.get(key), str) and t[key].count(mark) != 1:
                    errors.append(f"{code}.{key}: must contain {mark} exactly once")
        if isinstance(t.get("ai_tools_h"), str) and t["ai_tools_h"].count("{project}") != 1:
            errors.append(f"{code}.ai_tools_h: must contain {{project}} exactly once")
        if isinstance(t.get("post_edited"), str) and t["post_edited"].count("{names}") != 1:
            errors.append(f"{code}.post_edited: must contain {{names}} exactly once")
    return errors


def check_ai_tools(texts, ref, ai_tools):
    """data/ai_tools.yaml: every project has an entry, and every service a purpose, description and group.

    Project names are the same in every language, so a new project cannot be added to the
    language files without deciding here whether it gets a page of links for AI assistants.
    """
    errors = []
    names = [p.get("name") for p in ref.get("projects", []) if isinstance(p, dict)]
    for code, t in texts.items():
        other = [p.get("name") for p in t.get("projects", []) if isinstance(p, dict)]
        if other != names:
            errors.append(f"{code}.projects: names must be {names} (the same in every language)")
    projects = ai_tools.get("projects") or {}
    for name in names:
        if name not in projects:
            errors.append(f"data/ai_tools.yaml projects: add an entry for {name!r} (repo may be empty)")
    for name in projects:
        if name not in names:
            errors.append(f"data/ai_tools.yaml projects: {name!r} is not a project in data/i18n/{REFERENCE}.yaml")
    for name, p in projects.items():
        repo = (p or {}).get("repo") or ""
        if repo and not GITHUB_REPO.fullmatch(repo):
            errors.append(f"data/ai_tools.yaml {name}: repo must be owner/name, such as nguekwang/linguasim")
        if set(p or {}) - {"repo", "site"}:
            errors.append(f"data/ai_tools.yaml {name}: unknown fields {sorted(set(p) - {'repo', 'site'})}")
        url = (p or {}).get("site")
        if url is not None and not (isinstance(url, str) and url.startswith("https://")):
            errors.append(f"data/ai_tools.yaml {name}: site must be an https:// URL")
    slugs = [r.split("/")[1] for r in (ai_repo(p) for p in projects.values()) if GITHUB_REPO.fullmatch(r)]
    if len(set(slugs)) != len(slugs):
        errors.append("data/ai_tools.yaml projects: two repositories have the same name")
    services = ai_tools.get("services") or []
    ids = [s.get("id") for s in services]
    if len(set(ids)) != len(ids):
        errors.append("data/ai_tools.yaml services: duplicate ids")
    if set(ids) != set(ref.get("ai_tools_desc", {})):
        errors.append(f"data/ai_tools.yaml services: ids differ from data/i18n/{REFERENCE}.yaml ai_tools_desc")
    if set(ids) != set(ref.get("ai_tools_purpose", {})):
        errors.append(f"data/ai_tools.yaml services: ids differ from data/i18n/{REFERENCE}.yaml ai_tools_purpose")
    if {s.get("group") for s in services} != set(ref.get("ai_tools_groups", {})):
        errors.append(f"data/ai_tools.yaml services: groups differ from data/i18n/{REFERENCE}.yaml ai_tools_groups")
    for s in services:
        if not all(s.get(k) for k in ("id", "name", "host", "group")):
            errors.append(f"data/ai_tools.yaml services: {s.get('id')!r} needs id, name, host and group")
    return errors


def ai_repo(p):
    return (p or {}).get("repo") or ""


def project_sites(ai_tools):
    """The address where each project runs (`site` in data/ai_tools.yaml), by project name."""
    return {name: p["site"] for name, p in (ai_tools.get("projects") or {}).items() if (p or {}).get("site")}


def ai_tools_pages(site, ai_tools):
    """The projects that get a page of links for AI assistants, by project name.

    Each value has the page's path under /<lang>/, the repository URL and the services in
    display groups: [(group id, [(service, URL), ...]), ...].
    """
    groups = {}  # dicts keep insertion order: groups appear in the order of their first service
    for s in ai_tools.get("services") or []:
        groups.setdefault(s["group"], []).append(s)
    pages = {}
    for name, p in (ai_tools.get("projects") or {}).items():
        repo = ai_repo(p)
        if not repo:
            continue
        pages[name] = {
            "path": f"{AI_TOOLS_SLUG}/{repo.split('/')[1]}",
            "repo": f"https://github.com/{repo}",
            "groups": [(g, [(s, f"https://{s['host']}/{repo}") for s in items]) for g, items in groups.items()],
        }
    return pages


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


def text_dir(code):
    """Writing direction of a language ("rtl" or "ltr"), from its CLDR data in Babel, so no language file writes it."""
    return "rtl" if Locale.parse(code, sep="-").character_order == "right-to-left" else "ltr"


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


def local_digits(site, code, text):
    """Write 0-9 with the language's own digits when data/site.yaml `digits` lists them."""
    digits = site.get("digits", {}).get(code)
    if digits:
        text = text.translate(str.maketrans("0123456789", digits))
    return text


def updated_text(site, code, template, date):
    """Fill {date} with the month and year in the language's own format (e.g. 2026年11月)."""
    text = format_skeleton("yMMMM", date, locale=Locale.parse(code, sep="-"))
    return template.replace("{date}", local_digits(site, code, text))


def publications(site, code, t, pubs):
    """Return data/publications.yaml entries with this language's text around the titles.

    The template writes <title><en_space><en_open><title_en><en_after><note>, for example
    言語間の類似度の定量的な算出（A Quantitative Analysis of Cross-Linguistic Similarity）（2026）（卒業論文、非公開）.
    The brackets around the English title go inside one left-to-right isolate with it, so a
    right-to-left page that wraps the title keeps them on the right sides.
    """
    before, after = t["pub_title_en"].split("{title}")
    open_ = before.lstrip()
    space = before[:len(before) - len(open_)]
    out = []
    for p in pubs:
        details = [t["pub_types"][p["type"]]]
        if p.get("status"):
            details.append(t["pub_status"][p["status"]])
        note = (t["pub_note"].replace("{year}", local_digits(site, code, str(p["year"])))
                .replace("{details}", t["list_sep"].join(details)))
        out.append({"title": p["title"], "lang": p["lang"], "title_en": p.get("title_en"),
                    "en_space": space, "en_open": open_, "en_after": after, "note": note})
    return out


def check_publications(pubs, ref):
    errors = []
    for i, p in enumerate(pubs):
        where = f"data/publications.yaml publications[{i}]"
        for key in ("title", "lang", "year", "type"):
            if not p.get(key):
                errors.append(f"{where}: missing {key}")
        if p.get("lang") != "en" and not p.get("title_en"):
            errors.append(f"{where}: title_en is required when lang is not en")
        if p.get("type") not in ref.get("pub_types", {}):
            errors.append(f"{where}: type {p.get('type')!r} is not in pub_types of data/i18n/{REFERENCE}.yaml")
        if p.get("status") and p["status"] not in ref.get("pub_status", {}):
            errors.append(f"{where}: status {p['status']!r} is not in pub_status of data/i18n/{REFERENCE}.yaml")
        if set(p) - {"title", "lang", "title_en", "year", "type", "status"}:
            errors.append(f"{where}: unknown fields {sorted(set(p) - {'title', 'lang', 'title_en', 'year', 'type', 'status'})}")
    return errors


def main():
    global SITE_URL, OUT
    for arg in sys.argv[1:]:
        if arg.startswith("--out="):
            OUT = os.path.abspath(arg[len("--out="):])
    site = load("site.yaml")
    SITE_URL = site["url"].rstrip("/")
    texts = {}
    for code in site["languages"]:
        if os.path.exists(os.path.join(DATA, "i18n", code + ".yaml")):
            texts[code] = load("i18n", code + ".yaml")
    institutions = load("institutions.yaml") or {}
    post_editors = (load("post_editors.yaml") or {}).get("post_editors") or {}
    pubs = (load("publications.yaml") or {}).get("publications") or []
    ai_tools = load("ai_tools.yaml") or {}
    errors = check(site, texts, institutions, post_editors, ai_tools)
    if REFERENCE in texts:
        errors += check_publications(pubs, texts[REFERENCE])
    if errors:
        print(f"{len(errors)} problem(s) in data/:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    print(f"data OK: {len(texts)} languages share the structure of {REFERENCE}.yaml")
    for code, t in texts.items():
        t["dir"] = text_dir(code)
    if "--check" in sys.argv[1:]:
        return

    talks = (load("talks.yaml") or {}).get("talks") or []
    ai_pages = ai_tools_pages(site, ai_tools)
    sites = project_sites(ai_tools)
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
    # A pull request preview is the same site with noindex on every page (see templates/robots.html.j2).
    env.globals["preview"] = "--preview" in sys.argv[1:]
    # Content-Security-Policy and referrer policy of every page (templates/security.html.j2, tools/security_policy.py).
    env.globals["security_policies"] = lambda policy: security_policies(site, policy)
    env.globals["goatcounter_script"] = GOATCOUNTER_SCRIPT

    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "static"), OUT)
    write("robots.txt", env.get_template("robots.txt.j2").render(site=site))

    # The WebSite in the JSON-LD is one entity shared by every language, so it has one name.
    website_name = site_title(site, texts, None)
    page = env.get_template("page.html.j2")
    for code in site["languages"]:
        ja = code == "ja"
        t = texts[code]
        h1 = site["name"]["ja"] if ja else site["name"]["latin"]
        title = site_title(site, texts, code)
        html = page.render(
            site=site, langs=langs, talks=talks, code=code, t=t,
            h1=h1, title=title, site_name=site_title(site, texts, code), notice=notice(code, t, post_editors.get(code)),
            updated=updated_text(site, code, t["updated"], date), updated_url=updated_url,
            copyright_from=local_digits(site, code, str(site["copyright_from"])),
            jsonld=jsonld(site, code, t, title, website_name, post_editors.get(code)),
            alt_name=site["name"]["latin"] if ja else site["name"]["ja"],
            alt_lang="en" if ja else "ja",
            pubs=publications(site, code, t, pubs), names_slug=NAMES_SLUG, ai_pages=ai_pages, project_sites=sites,
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
        title = f"{t['names_h']} – {site_title(site, texts, code)}"
        sub = {"path": NAMES_SLUG, "name": t["names_h"], "description": t["names_intro"]}
        write(os.path.join(code, NAMES_SLUG, "index.html"), names_page.render(
            site=site, langs=langs, code=code, t=t, rows=rows, path=NAMES_SLUG, up="../../", home="../",
            description=t["names_intro"], title=title, site_name=site_title(site, texts, code),
            notice=notice(code, t, post_editors.get(code)),
            jsonld=jsonld(site, code, t, title, website_name, post_editors.get(code), sub=sub),
            updated=updated_text(site, code, t["updated"], date), updated_url=updated_url,
            copyright_from=local_digits(site, code, str(site["copyright_from"])),
            footer_name=site["name"]["ja"] if code == "ja" else site["name"]["latin_short"],
        ))

    ai_page = env.get_template("ai_tools.html.j2")
    for name, p in ai_pages.items():
        for code in site["languages"]:
            t = texts[code]
            heading = t["ai_tools_h"].replace("{project}", name)
            title = f"{heading} – {site_title(site, texts, code)}"
            sub = {"path": p["path"], "name": heading, "description": t["ai_tools_intro"]}
            write(os.path.join(code, *p["path"].split("/"), "index.html"), ai_page.render(
                site=site, langs=langs, code=code, t=t, project=name, p=p, path=p["path"], up="../../../", home="../../",
                description=t["ai_tools_intro"], title=title, site_name=site_title(site, texts, code),
                notice=notice(code, t, post_editors.get(code)),
                jsonld=jsonld(site, code, t, title, website_name, post_editors.get(code), sub=sub),
                updated=updated_text(site, code, t["updated"], date), updated_url=updated_url,
                copyright_from=local_digits(site, code, str(site["copyright_from"])),
                footer_name=site["name"]["ja"] if code == "ja" else site["name"]["latin_short"],
            ))

    codes = site["languages"]
    en = texts[REFERENCE]
    write("index.html", env.get_template("root.html.j2").render(
        site=site, langs=langs, title=website_name, site_name=website_name, description=en["desc"],
        jsonld=jsonld(site, None, en, website_name, website_name)))
    write("llms.txt", env.get_template("llms.txt.j2").render(
        site=site, langs=langs, t=en, pubs=publications(site, REFERENCE, en, pubs), ai_pages=ai_pages,
        project_sites=sites))
    subpages = [NAMES_SLUG] + [p["path"] for p in ai_pages.values()]
    write("sitemap.xml", env.get_template("sitemap.xml.j2").render(site=site, codes=codes, subpages=subpages))
    print(f"built {len(codes)} language pages (and their sub-pages: {', '.join(subpages)}) into {os.path.relpath(OUT, ROOT)}/")

    if "--no-pdf" in sys.argv[1:]:
        print("skipped the CV PDFs (--no-pdf); the CV links on the pages point to missing files")
        return
    cv = env.get_template("cv.html.j2")
    with tempfile.TemporaryDirectory() as tmp:
        # The CV's stylesheet sits next to the temporary HTML files, so the policy can keep style-src 'self'.
        shutil.copy(os.path.join(ROOT, "templates", "cv.css"), tmp)
        jobs = []
        for code in codes:
            ja = code == "ja"
            t = texts[code]
            src = os.path.join(tmp, code + ".html")
            with open(src, "w", encoding="utf-8") as f:
                f.write(cv_html := cv.render(
                    site=site, talks=talks, code=code, t=t,
                    h1=site["name"]["ja"] if ja else site["name"]["latin"],
                    alt_name=site["name"]["latin"] if ja else site["name"]["ja"],
                    alt_lang="en" if ja else "ja",
                    pubs=publications(site, code, t, pubs), project_sites=sites,
                    updated=updated_text(site, code, t["updated"], date),
                    notice=notice(code, t, post_editors.get(code)),
                ))
            # The CV is not published, but it gets the same checks as every page (tools/security_check.py).
            problems = check_page(cv_html, security_policies(site, "cv"))
            if problems:
                raise SystemExit(f"CV ({code}) fails the security check:\n  " + "\n  ".join(problems))
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



def site_title(site, texts, code):
    """The site's name in one language: the owner's name, a dash and `site_title`.

    The Japanese pages use the Japanese name; every other page uses `latin_title`
    (surname first). The root language chooser (code None) uses English. Page titles,
    og:site_name and the WebSite name in the JSON-LD all use it.
    """
    name = site["name"]["ja"] if code == "ja" else site["name"]["latin_title"]
    return f"{name} – {texts[code or REFERENCE]['site_title']}"

def jsonld(site, code, t, title, website_name, post_editors=None, sub=None):
    """Structured data (schema.org JSON-LD) for one page.

    Every page describes the same Person and WebSite (same @id), so search engines and
    AI assistants can join the language versions into one entity. `code` is None for the
    root language chooser. With `sub` ({path, name, description}), the page is the sub-page
    /<code>/<path>/ (such as the institution-names page): a WebPage about the Person, with a
    breadcrumb back to the language's profile page, instead of the ProfilePage itself. Post-editors of the page's
    language are listed as `contributor` of the page. `website_name` is the WebSite's
    name, the same on every page.
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
        "knowsAbout": [t["keywords"][k] for k in keyword_ids(site)],
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
        "name": website_name,
        "inLanguage": site["languages"],
        "about": {"@id": f"{base}/#person"},
    }
    graph = [website, person]
    if code is not None and sub is not None:
        home = f"{base}/{code}/"
        url = f"{home}{sub['path']}/"
        home_name = name["ja"] if code == "ja" else name["latin"]
        graph.insert(0, {
            "@type": "WebPage",
            "@id": f"{url}#page",
            "url": url,
            "name": title,
            "description": sub["description"],
            "inLanguage": code,
            "isPartOf": {"@id": f"{base}/#website"},
            "about": {"@id": f"{base}/#person"},
            "breadcrumb": {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": home_name, "item": home},
                    {"@type": "ListItem", "position": 2, "name": sub["name"], "item": url},
                ],
            },
        })
    elif code is not None:
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
    if code is not None and post_editors:
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
