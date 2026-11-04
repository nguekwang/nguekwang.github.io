---
paths:
  - "tools/**"
  - ".github/**"
  - "requirements.txt"
---

# Build and CI

- `pip install -r requirements.txt`, then `python3 tools/build.py --check` checks the data, and `python3 tools/build.py` checks and builds the site into `_site/`. Generated HTML is not committed.
- GitHub Actions (`.github/workflows/site.yml`) runs the check and build on every pull request, and on push to `main` builds and deploys to GitHub Pages.
- The check must fail on any difference between language files (missing or extra keys, different list lengths or keyword ids). Do not weaken it.
- The footer's "last updated" date and link come from git: the build fills `{date}` with the date of the latest commit that changed `data/`, `templates/`, `static/` or `tools/` (formatted per language with Babel) and links to that commit on GitHub. The workflow checks out full history (`fetch-depth: 0`) for this.
- Every page carries a title, description, Open Graph tags, canonical and hreflang links, and schema.org JSON-LD (`ProfilePage`, `WebSite`, `Person`) built by `jsonld()` in `tools/build.py`. All pages share the same `Person` `@id`, so the language versions read as one person.
