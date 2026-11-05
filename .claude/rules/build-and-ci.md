---
paths:
  - "tools/**"
  - ".github/**"
  - "requirements*.txt"
  - "lychee.toml"
---

# Build and CI

- `pip install -r requirements.txt`, then `python3 tools/build.py --check` checks the data, and `python3 tools/build.py` checks and builds the site into `_site/`. Generated HTML is never committed: GitHub Pages publishes from GitHub Actions, not from a branch.
- GitHub Actions (`.github/workflows/site.yml`) runs the check and build on every pull request, and on push to `main` builds and deploys to GitHub Pages.
- The check must fail on any difference between language files (missing or extra keys, different list lengths or keyword ids). Do not weaken it.
- The footer's "last updated" date and link come from git: the build fills `{date}` with the date of the latest commit that changed `data/`, `templates/`, `static/` or `tools/` (formatted per language with Babel) and links to that commit on GitHub. The workflow checks out full history (`fetch-depth: 0`) for this.
- Every page carries a title, description, Open Graph tags, canonical and hreflang links, and schema.org JSON-LD (`ProfilePage`, `WebSite`, `Person`) built by `jsonld()` in `tools/build.py`. All pages share the same `Person` `@id`, so the language versions read as one person.

## Automated checks

- `tools/privacy_check.py` (CI, every pull request): fails on email addresses, phone numbers, postal codes or street addresses, and full birth dates that are not in the allow list `data/privacy.yaml`. Add to the allow list only what the owner has approved.
- `tools/check_links.py` (CI, every pull request): fails when a link between the site's own pages, or an entry in `sitemap.xml`, points at a file that is not built.
- `.github/workflows/links.yml` (weekly): checks links to other sites with lychee (`lychee.toml`) and opens or updates the issue "Broken links on the site". Links listed in `data/post_editors.yaml` are skipped, so they never appear in a public issue.
- `.github/workflows/screenshots.yml` (pull requests that touch `data/`, `templates/`, `static/`, `tools/` or requirements): before/after screenshots by `tools/screenshots.py`, uploaded as an artifact and summarised in a pull request comment.
- `.github/dependabot.yml`: weekly pull requests for new versions of GitHub Actions and Python packages. The owner reviews and merges them like any other pull request.
