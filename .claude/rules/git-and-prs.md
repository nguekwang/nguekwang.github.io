# Git and pull requests

## Branches

- Never push to `main` directly. Create a branch and open a pull request for every change, so the owner can review it first.
- Start every branch from the latest `main`. Do not build a branch on top of another open pull request.
- Never rebase and never force-push. Rebasing rewrites history, which can break other branches and lose changes.
- If `main` moves on and the pull request conflicts with it (for example after another pull request was merged), merge `main` into the branch and fix the conflict in a merge commit.

## Before pushing

- Run `python3 tools/build.py --check`, `python3 tools/privacy_check.py`, `python3 tools/build.py` and `python3 tools/check_links.py`. All must pass (CI runs the same steps).
- Check the diff for personal information the owner has not approved (see `publishing.md`). `tools/privacy_check.py` is a safety net, not a replacement for this check. Add to its allow list (`data/privacy.yaml`) only what the owner has approved.

## Pull requests

- Title and description in English.
- For any visible change, the pull request needs before and after screenshots (at least the Japanese page and one right-to-left page such as Arabic). The `screenshots` workflow takes them (Japanese and every right-to-left language, desktop and mobile) and keeps a comment on the pull request with a table of changed pages and a link to the images. Look at the images and mention anything unexpected in the description; do not take them by hand unless the workflow cannot run.
- Watch CI on the pull request and fix failures until it passes. Do not skip or weaken a check to make it pass.
- The owner reviews and merges. Do not merge your own pull request.
- If you open a new pull request that replaces an older one, say in the report that the older one can be closed.
