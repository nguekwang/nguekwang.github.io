---
paths:
  - "data/**"
---

# Data (`data/`)

All page text lives here as YAML. HTML structure is in `templates/`.

- `data/site.yaml`: site-wide settings, names, language order (`languages`), keyword order. Page titles are `<name> – <site_title>` (built by `site_title()` in `tools/build.py`): `site_title` is page text in each language file, and the name is `name.ja` on Japanese pages and `name.latin_title` (surname first, the owner's choice) elsewhere.
- `data/i18n/<code>.yaml`: all page text for one language.
- `data/talks.yaml`: talks (language-independent).
- `data/publications.yaml`: publications and theses (see below).
- `data/institutions.yaml`: institution names per language (official or translated).
- `data/post_editors.yaml`: native speakers who post-edited a machine-translated language (see `writing-style.md`).
- `data/privacy.yaml`: allow list for `tools/privacy_check.py` (see `build-and-ci.md`).

## Every language has the same items

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Every language file must have exactly the same keys, list lengths and keyword ids as `en.yaml`. Only `mt_notice` may be empty (see `writing-style.md`).
- When adding a key or a list item, add it to every language file in the same change. `python3 tools/build.py --check` (and CI) fails otherwise. Fix the data; never add a fallback.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- To add a language: copy `data/i18n/en.yaml` to `data/i18n/<code>.yaml`, translate every value, and add the code to `languages`.

## Values that are not page text

- `updated` in each language file is only a label with one `{date}` placeholder. The date comes from git (see `build-and-ci.md`); never write a date in the YAML.
- `same_as` in `data/site.yaml` lists the owner's other profiles for the JSON-LD (GitHub now; add ORCID and researchmap when they exist).
- `verification` in `data/site.yaml` holds the Google Search Console and Bing Webmaster Tools tokens (HTML meta tag method).

## Publications

- Every publication or thesis is one entry in `data/publications.yaml`, newest first. Never write one into a template or a language file. The build lists every entry on every language page, in the CV and in `llms.txt`.
- Each entry has the title as written (`title`, `lang`), the English title (`title_en`, required when the title is not English), `year`, `type` and optional `status`. Every language shows both titles.
- A line reads `<title> (<English title>) (<year>) (<type>, <status>)`, as the owner asked, with no label in front; for example `言語間の類似度の定量的な算出（A Quantitative Analysis of Cross-Linguistic Similarity）（2026）（卒業論文、非公開）`.
- The brackets, comma and spacing come from `pub_title_en`, `pub_note` and `list_sep` in each language file, written as that language's modern official documents write them. The year uses the language's digits (`digits` in `data/site.yaml`).
- A new `type` or `status` needs a translation under `pub_types` or `pub_status` in every language file in the same change; `python3 tools/build.py --check` fails otherwise.
