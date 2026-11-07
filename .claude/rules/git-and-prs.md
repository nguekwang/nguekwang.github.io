# Git and pull requests

The shared rule is `git-and-prs.md` in the `research-aide` repository (branches, no rebase or force-push, merge commits, the owner merges). Here:

## Before pushing

- Run `python3 tools/build.py --check`, `python3 tools/privacy_check.py`, `python3 tools/build.py` and `python3 tools/check_links.py`. All must pass (CI runs the same steps).
- `tools/privacy_check.py` is a safety net, not a replacement for checking the diff yourself (see `publishing.md`). Add to its allow list (`data/privacy.yaml`) only what the owner has approved.

## Pull requests

- For any visible change, the pull request needs before and after screenshots (at least the Japanese page and one right-to-left page such as Arabic). The `screenshots` workflow takes them (Japanese and every right-to-left language, desktop and mobile) and keeps a comment on the pull request with a table of changed pages and a link to the images. Look at the images and mention anything unexpected in the description; do not take them by hand unless the workflow cannot run.
- Every pull request from this repository gets a preview of the site at `/preview/pr-<number>/`, and `pages.yml` keeps a comment on the pull request with its links (see `build-and-ci.md` and `pr-previews.md` in `research-aide`). Point the owner to that comment in the report; do not post preview links by hand.
