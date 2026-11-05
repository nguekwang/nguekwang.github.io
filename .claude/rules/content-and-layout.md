# Content and layout

## Languages

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- `python3 tools/build.py --check` (and CI) fails when a language file is missing a key, has an extra one, or has a list of a different length. Fix the data; never add a fallback.

## Digits

Digits follow the language's modern official documents, like all other notation (see `CLAUDE.md`). Current choices and their basis:

- Persian (`fa`): Persian digits (۰-۹), as in Iranian government documents.
- Hindi (`hi`): 0-9. Article 343(1) of the Constitution of India makes "the international form of Indian numerals" (0-9) the form for the Union's official purposes.
- Arabic (`ar`): 0-9. Official documents differ by country: governments in parts of the Mashriq and the Gulf use Arabic-Indic digits (٠-٩), while the Maghreb uses 0-9. The site does not target one country, so it follows the Arabic official documents of the United Nations, which use 0-9.
- Thai (`th`): Thai government documents use Thai digits (๐-๙). The page still uses 0-9 until the owner decides whether to switch.
- Every other language: 0-9.

How to apply a choice:

- Write the digits directly in `data/i18n/<code>.yaml`, and list the language under `digits` in `data/site.yaml` so the dates the build generates (such as "last updated") match.
- Do not convert digits in whole strings at build time: identifiers such as "i18n" must keep 0-9.
- To change a language's digits, change its YAML text and its `digits` entry together, and update the list above.

## Layout and style

- Fix layout and style once, in the shared template (`templates/`) or stylesheet (`static/style.css`). Never patch a single page, a single language or a single link.

## What may be published

- Publish only what the owner has explicitly approved.
- Do not present other people's work (projects, fonts, writing) as the owner's, and do not commit files the owner has no right to redistribute.
- Data that must stay private, such as measurement results and plans, is kept outside this public repository.
