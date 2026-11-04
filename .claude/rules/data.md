---
paths:
  - "data/**"
---

# Data (`data/`)

All page text lives here as YAML. HTML structure is in `templates/`.

- `data/site.yaml`: site-wide settings, names, language order (`languages`), keyword order.
- `data/i18n/<code>.yaml`: all page text for one language.
- `data/talks.yaml`: talks (language-independent).
- `data/institutions.yaml`: institution names per language (official or translated).

## Every language has the same items

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Every language file must have exactly the same keys, list lengths and keyword ids as `en.yaml`. Only `mt_notice` may be empty.
- When adding a key or a list item, add it to every language file in the same change. `python3 tools/build.py --check` (and CI) fails otherwise. Fix the data; never add a fallback.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- To add a language: copy `data/i18n/en.yaml` to `data/i18n/<code>.yaml`, translate every value, and add the code to `languages`.

## Values that are not page text

- `updated` in each language file is only a label with one `{date}` placeholder. The date comes from git (see `build-and-ci.md`); never write a date in the YAML.
- `same_as` in `data/site.yaml` lists the owner's other profiles for the JSON-LD (GitHub now; add ORCID and researchmap when they exist).
- `verification` in `data/site.yaml` holds the Google Search Console and Bing Webmaster Tools tokens (HTML meta tag method).
