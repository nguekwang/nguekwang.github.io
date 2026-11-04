# Content and layout

## Languages

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- `python3 tools/build.py --check` (and CI) fails when a language file is missing a key, has an extra one, or has a list of a different length. Fix the data; never add a fallback.

## Layout and style

- Fix layout and style once, in the shared template (`templates/`) or stylesheet (`static/style.css`). Never patch a single page, a single language or a single link.

## What may be published

- Publish only what the owner has explicitly approved.
- Do not present other people's work (projects, fonts, writing) as the owner's, and do not commit files the owner has no right to redistribute.
- Data that must stay private, such as measurement results and plans, is kept outside this public repository.
