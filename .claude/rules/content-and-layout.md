# Content and layout

## Languages

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- `python3 tools/build.py --check` (and CI) fails when a language file is missing a key, has an extra one, or has a list of a different length. Fix the data; never add a fallback.

## Machine translation and post-editors

- English, Japanese and Spanish are written by the owner; their `mt_notice` is empty. Every other language is machine-translated and must show `mt_notice`.
- A native speaker may post-edit (review and correct) a machine-translated language. List them in `data/post_editors.yaml`; that language's pages then show `post_edited` with their names instead of `mt_notice`.
- Add a person only after they agree to be named, with the name and the one link (social media, website or GitHub) they chose. Never commit their contact details; the build rejects any field other than `name` and `url`.
- Claude does not contact possible post-editors. Claude may draft the request; the owner sends it.
- `.github/workflows/post-editor-links.yml` checks the post-editors' links weekly and emails the owner through Gmail when one breaks. Never report these links in an issue, and keep names and URLs out of public workflow logs.
- Do not overwrite a post-edited language with a new machine translation of the whole file. Translate only the changed text and ask the owner to have the post-editor check it.

## Layout and style

- Fix layout and style once, in the shared template (`templates/`) or stylesheet (`static/style.css`). Never patch a single page, a single language or a single link.

## What may be published

- Publish only what the owner has explicitly approved.
- Do not present other people's work (projects, fonts, writing) as the owner's, and do not commit files the owner has no right to redistribute.
- Data that must stay private, such as measurement results and plans, is kept outside this public repository.
