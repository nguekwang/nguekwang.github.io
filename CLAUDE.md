# CLAUDE.md

Guidance for Claude (and other contributors) working in this repository.

## Language: English first

This repository should read as one whose first language is English.

- Write everything in English: code comments, docstrings, YAML comments, workflow files, commit messages, PR titles and descriptions, and any new docs.
- Japanese is allowed only in:
  - page text for the Japanese version (the values in `data/i18n/ja.yaml`, and `title_ja` in `data/site.yaml`);
  - personal names (e.g. `松浦 義広`) and language names in the language menu (e.g. `日本語`).
- Other languages' page text lives in their own `data/i18n/<code>.yaml` files and stays in that language.
- This rule covers repository contents only. Chat with the owner (Claude replies, questions, reports) is in Japanese.

## Git workflow

- Never push to `main` directly. Create a branch and open a pull request for every change, so the owner can review it first.
- Before committing, check that nothing personal is added beyond what the site already shows publicly (no phone number, address, birth date, or private email addresses).

## Content rules

- Do not add a `README.md`.
- Do not add content about other people's projects as if they were the owner's work, and do not commit fonts or files the owner has no right to redistribute.

## Building

All page text lives in YAML under `data/`; HTML structure lives in `templates/`. Generated HTML is not committed.

- `data/site.yaml`: site-wide settings, names, language order, keyword order.
- `data/i18n/<code>.yaml`: all page text for one language. Every language file must have exactly the same keys, list lengths and keyword ids as `en.yaml`, so that every language shows the same items. Only `mt_notice` may be empty.
- `data/talks.yaml`: talks (language-independent).
- `static/`: files copied as they are (CSS, JS, robots.txt).
- `pip install -r requirements.txt`, then `python3 tools/build.py --check` checks the data, and `python3 tools/build.py` checks and builds the site into `_site/`.
- GitHub Actions (`.github/workflows/site.yml`) runs the check and build on every pull request, and on push to `main` builds and deploys to GitHub Pages.
- When adding a key or a list item, add it to every language file in the same change, or the check fails.

## Search engines and AI assistants

- Every page carries a title, description, Open Graph tags, canonical and hreflang links, and schema.org JSON-LD (`ProfilePage`, `WebSite`, `Person`) built by `jsonld()` in `tools/build.py`. All pages share the same `Person` `@id`, so the language versions read as one person.
- `same_as` in `data/site.yaml` lists the owner's other profiles (GitHub now; add ORCID and researchmap when they exist).
- `verification` in `data/site.yaml` holds the Google Search Console and Bing Webmaster Tools tokens (HTML meta tag method).
- `_site/llms.txt` is a plain-text English summary for AI assistants, generated from `data/i18n/en.yaml`.

## Measurement (GoatCounter)

- Page views are counted by GoatCounter (`goatcounter` in `data/site.yaml`). Links we share carry a campaign tag, e.g. `?ref=card` (business card QR) or `?ref=github`.
- Conversions are clicks on links marked with `data-cv="<name>"` in `templates/page.html.j2`. `static/cv.js` sends each one as the GoatCounter event `cv-<name>`, with the visit's `?ref=` as its referrer, and keeps `?ref=` on language menu links.
- Current names: `email-top`, `email-contact`, `github-top`, `github-contact`, `talk`, `request-lang`. When adding a link to another profile (ORCID, researchmap), give it a `data-cv` name too.
- The measurement plan and the list of initiatives (施策) are kept outside this public repository.
