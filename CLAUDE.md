# CLAUDE.md

Guidance for Claude (and other contributors) working in this repository.

## Language: English first

This repository should read as one whose first language is English.

- Write everything in English: code comments, docstrings, TOML comments, workflow files, commit messages, PR titles and descriptions, and any new docs.
- Japanese is allowed only in:
  - page text for the Japanese version (`ja/`, the values in `data/i18n/ja.toml`, `ja = ...` entries in `data/keywords.toml`, `title_ja` in `data/site.toml`);
  - personal names (e.g. `松浦 義広`) and language names in the language menu (e.g. `日本語`).
- Other languages' page text lives in their own `data/i18n/<code>.toml` files and stays in that language.
- This rule covers repository contents only. Chat with the owner (Claude replies, questions, reports) is in Japanese.

## Git workflow

- Never push to `main` directly. Create a branch and open a pull request for every change, so the owner can review it first.
- Before committing, check that nothing personal is added beyond what the site already shows publicly (no phone number, address, birth date, or private email addresses).

## Content rules

- Do not add a `README.md`.
- Do not add content about other people's projects as if they were the owner's work, and do not commit fonts or files the owner has no right to redistribute.

## Building

All page text lives in `data/`. Do not edit the generated HTML by hand.

- `python3 -I tools/build.py` regenerates every `<lang>/index.html`, the root `index.html`, and `sitemap.xml`.
- On push to `main`, GitHub Actions (`.github/workflows/build.yml`) rebuilds and commits the pages when `data/` or `tools/` changes.
- After a change that should not affect the pages (for example, comments only), rebuild and confirm there is no HTML diff.
