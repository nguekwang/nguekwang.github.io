# Content and layout

## Languages

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- `python3 tools/build.py --check` (and CI) fails when a language file is missing a key, has an extra one, or has a list of a different length. Fix the data; never add a fallback.

## Digits

- Western digits (0-9) are the default in every language, including Arabic, Hindi and Thai. Unicode CLDR uses them for Arabic without a region (`ar`), and major Arabic sites (Al Jazeera, the UN, King Saud University) write years with 0-9. Arabic-Indic digits are only the regional default in parts of the Mashriq and the Gulf, while the Maghreb uses 0-9.
- Persian (`fa`) is the exception: Persian text is written with Persian digits (۰-۹). Write them directly in `data/i18n/fa.yaml`, and the build converts the "last updated" date through `digits` in `data/site.yaml`.
- Do not convert digits in whole strings at build time: identifiers such as "i18n" must keep 0-9.
- To change a language's digits, change its YAML text and its `digits` entry together, so the page and the footer match.

## Layout and style

- Fix layout and style once, in the shared template (`templates/`) or stylesheet (`static/style.css`). Never patch a single page, a single language or a single link.

## What may be published

- Publish only what the owner has explicitly approved.
- Do not present other people's work (projects, fonts, writing) as the owner's, and do not commit files the owner has no right to redistribute.
- Data that must stay private, such as measurement results and plans, is kept outside this public repository.
