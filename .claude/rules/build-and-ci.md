---
paths:
  - "tools/**"
  - ".github/**"
  - "requirements*.txt"
  - "lychee.toml"
  - "templates/cv.html.j2"
---

# Build and CI

- `pip install -r requirements.txt`, then `python3 tools/build.py --check` checks the data, and `python3 tools/build.py` checks and builds the site into `_site/`. Generated HTML is never committed: GitHub Pages publishes from GitHub Actions, not from a branch.
- The build also makes a CV for every language at `/<lang>/<cv_file>` (`cv_file` in `data/site.yaml`): `templates/cv.html.j2` is printed to PDF with headless Chrome (set `CHROME` if it is not on `PATH`; `--no-pdf` skips it). The CV shows only what the profile page shows, so it never adds personal details of its own; when a page section changes shape, update the CV template in the same change. CI installs the Noto fonts it needs.
- `.github/workflows/site.yml` runs the check and build on every pull request. `.github/workflows/pages.yml` is the only workflow that deploys to GitHub Pages; keep it that way, because each deployment replaces the whole site.
- Pull request previews: for pull requests from this repository (not forks or Dependabot), `site.yml` also builds `python3 tools/build.py --preview --no-pdf --out=_preview` (every page gets `<meta name="robots" content="noindex">` from `templates/robots.html.j2`; the CV PDFs are copied from `_site/`) and uploads it as the artifact `preview`. `pages.yml` runs on push to `main`, after each passing `site.yml` run for a pull request, and when a pull request is closed: it builds `main`, adds the latest passing preview of every open pull request at `/preview/pr-<number>/`, deploys, and keeps one comment on each pull request (marker `<!-- preview-bot -->`) linking the Japanese, Arabic, English and language-chooser pages with `?ref=pr-<number>`. It never runs pull request code; it only unpacks the checked artifact.
- The check must fail on any difference between language files (missing or extra keys, different list lengths or keyword ids). Do not weaken it.
- The footer's "last updated" date and link come from git: the build fills `{date}` with the date of the latest commit that changed `data/`, `templates/`, `static/` or `tools/` (formatted per language with Babel) and links to that commit on GitHub. The workflow checks out full history (`fetch-depth: 0`) for this.
- Every page carries a title, description, Open Graph tags, canonical and hreflang links, and schema.org JSON-LD built by `jsonld()` in `tools/build.py`: `ProfilePage`, `WebSite` and `Person` on each language's main page, and `WebPage` (with a `BreadcrumbList` back to the main page), `WebSite` and `Person` on sub-pages such as `/<lang>/institution-names/` and `/<lang>/ai-tools/<repo name>/`. Every sub-page is listed in `sitemap.xml`. All pages share the same `Person` `@id`, so the language versions read as one person.

## Automated checks

- `tools/privacy_check.py` (CI, every pull request): fails on email addresses, phone numbers, postal codes or street addresses, and full birth dates that are not in the allow list `data/privacy.yaml`. Add to the allow list only what the owner has approved.
- `tools/check_links.py` (CI, every pull request): fails when a link between the site's own pages, or an entry in `sitemap.xml`, points at a file that is not built.
- `.github/workflows/links.yml` (weekly): checks links to other sites with lychee (`lychee.toml`) and opens or updates the issue "Broken links on the site". Links listed in `data/post_editors.yaml` are skipped, so they never appear in a public issue.
- `.github/workflows/screenshots.yml` (pull requests that touch `data/`, `templates/`, `static/`, `tools/` or requirements): before/after screenshots by `tools/screenshots.py`, uploaded as an artifact and summarised in a pull request comment.
- `.github/workflows/browsers.yml` (same pull requests): `tools/browser_check.py` opens every page of every language at desktop and phone width in Chromium, Firefox and WebKit, and fails on sideways scrolling, a language menu outside the window, or a JavaScript or console error. Rules: `css-and-browsers.md`.
- `.github/dependabot.yml`: weekly pull requests for new versions of GitHub Actions and Python packages. The owner reviews and merges them like any other pull request.
