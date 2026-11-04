#!/usr/bin/env python3
"""Static site generator for this site.

All page text lives in YAML under data/:
  data/site.yaml          site-wide settings, names, language order, keyword order
  data/i18n/<code>.yaml   page text for one language
  data/talks.yaml         talks (language-independent)
HTML structure lives in templates/. This script only joins the two.

Usage:
  python3 tools/build.py            check the data, then build the site into _site/
  python3 tools/build.py --check    check the data only

The check fails when any language file differs in structure from data/i18n/en.yaml
(missing or extra keys, different list lengths, empty text), so every language shows the same items.
"""
import json, os, shutil, sys, urllib.parse

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "_site")
REFERENCE = "en"
# Keys whose value may be an empty string (an empty value means "do not show").
MAY_BE_EMPTY = {"mt_notice"}


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


def check(site, texts):
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
    return errors


def main():
    site = load("site.yaml")
    texts = {}
    for code in site["languages"]:
        if os.path.exists(os.path.join(DATA, "i18n", code + ".yaml")):
            texts[code] = load("i18n", code + ".yaml")
    errors = check(site, texts)
    if errors:
        print(f"{len(errors)} problem(s) in data/:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    print(f"data OK: {len(texts)} languages share the structure of {REFERENCE}.yaml")
    if "--check" in sys.argv[1:]:
        return

    talks = (load("talks.yaml") or {}).get("talks") or []
    langs = [{"code": c, "native": texts[c]["native"]} for c in site["languages"]]
    req = site["translation_request"]
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
            h1=h1, title=title,
            jsonld=jsonld(site, code, t, title),
            alt_name=site["name"]["latin"] if ja else site["name"]["ja"],
            alt_lang="en" if ja else "ja",
            thesis_title=site["thesis"]["title_ja"] if ja else site["thesis"]["title_en"],
            thesis_lang="ja" if ja else "en",
            footer_name=site["name"]["ja"] if ja else site["name"]["latin_short"],
            request_mailto=f"mailto:{site['email']}?subject={urllib.parse.quote(req['subject'])}&body={urllib.parse.quote(req['body'])}",
        )
        write(os.path.join(code, "index.html"), html)

    codes = site["languages"]
    en = texts[REFERENCE]
    write("index.html", env.get_template("root.html.j2").render(
        site=site, langs=langs, title=site["name"]["latin"], description=en["desc"],
        jsonld=jsonld(site, None, en, site["name"]["latin"])))
    write("llms.txt", env.get_template("llms.txt.j2").render(
        site=site, langs=langs, t=en, keywords=[en["keywords"][k] for k in site["keywords"]]))
    write("sitemap.xml", env.get_template("sitemap.xml.j2").render(site=site, codes=codes))
    print(f"built {len(codes)} language pages into _site/")


def jsonld(site, code, t, title):
    """Structured data (schema.org JSON-LD) for one page.

    Every page describes the same Person and WebSite (same @id), so search engines and
    AI assistants can join the language versions into one entity. `code` is None for the
    root language chooser.
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
    data = {"@context": "https://schema.org", "@graph": graph}
    # Escape "</" so the JSON can never close the surrounding <script> element.
    return Markup(json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/"))


def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
