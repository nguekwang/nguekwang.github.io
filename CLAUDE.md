# CLAUDE.md

Guidance for Claude (and other contributors) working in this repository.

More detailed rules are in `.claude/rules/` (Claude Code loads them together with this file):

- `working-with-the-owner.md`: how to start a task, ask questions, and report back.
- `git-and-prs.md`: branches, conflicts, checks and pull requests.
- `content-and-layout.md`: rules for page content, languages and styling.

## Language: English first

This repository should read as one whose first language is English.

- Write everything in English: code comments, docstrings, YAML comments, workflow files, commit messages, PR titles and descriptions, and any new docs.
- Japanese is allowed only in:
  - page text for the Japanese version (the values in `data/i18n/ja.yaml`, and `title_ja` in `data/site.yaml`);
  - personal names (e.g. `松浦 義広`) and language names in the language menu (e.g. `日本語`).
- Other languages' page text lives in their own `data/i18n/<code>.yaml` files and stays in that language.
- This rule covers repository contents only. Chat with the owner (Claude replies, questions, reports) is in Japanese.

## Git workflow

- Never push to `main` directly. Create a branch and open a pull request for every change, so the owner can review it first. The owner merges.
- Start every branch from the latest `main`. Never rebase and never force-push. Details: `.claude/rules/git-and-prs.md`.
- Publish only personal information the owner has explicitly approved. Before committing, check that nothing else personal is added (no phone number, address, full birth date, or private email addresses). The birth month and year and home city in the background section were added at the owner's request.

## Content rules

- Do not add a `README.md`.
- Links that leave the site open in a new tab. The build adds `target="_blank" rel="noopener noreferrer"` to every `http(s)` link outside `site.url` (see `open_external_in_new_tab()` in `tools/build.py`), so do not write `target` or `rel` on links in templates. `mailto:` links, in-page anchors and links between the site's own pages (such as the language menu) stay in the same tab.
- Switching language must not add a browser history entry, so Back goes to the page before, not to the previous language. `static/lang.js` fetches the other language version and swaps it in with `history.replaceState()` (falling back to `location.replace()`); the URL still shows `/<lang>/`. Keep every language as its own static page with ordinary links, so search engines and visitors without JavaScript still get them. Pages that use it need `connect-src 'self'` in their Content-Security-Policy.
- Do not add content about other people's projects as if they were the owner's work, and do not commit fonts or files the owner has no right to redistribute.

## Building

All page text lives in YAML under `data/`; HTML structure lives in `templates/`. Generated HTML is not committed.

- `data/site.yaml`: site-wide settings, names, language order, keyword order.
- `data/i18n/<code>.yaml`: all page text for one language. Every language file must have exactly the same keys, list lengths and keyword ids as `en.yaml`, so that every language shows the same items. Only `mt_notice` may be empty.
- `data/talks.yaml`: talks (language-independent).
- `data/post_editors.yaml`: native speakers who post-edited a machine-translated language. Rules: `.claude/rules/content-and-layout.md`.
- `static/`: files copied as they are (CSS, JS, robots.txt).
- `pip install -r requirements.txt`, then `python3 tools/build.py --check` checks the data, and `python3 tools/build.py` checks and builds the site into `_site/`.
- GitHub Actions (`.github/workflows/site.yml`) runs the check and build on every pull request, and on push to `main` builds and deploys to GitHub Pages.
- The footer's "last updated" date and link come from git, not from the YAML: `updated` in each language file is a label with one `{date}` placeholder, which the build fills with the date of the latest commit that changed `data/`, `templates/`, `static/` or `tools/` (formatted per language with Babel) and links to that commit on GitHub. The workflow checks out full history (`fetch-depth: 0`) for this.
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
