# Git and pull requests

## Branches

- Never push to `main` directly. Create a branch and open a pull request for every change, so the owner can review it first.
- Start every branch from the latest `main`. Do not build a branch on top of another open pull request.
- Never rebase and never force-push. Rebasing rewrites history, which can break other branches and lose changes.
- If `main` moves on and the pull request conflicts with it (for example after another pull request was merged), merge `main` into the branch and fix the conflict in a merge commit.

## Before pushing

- Run `python3 tools/build.py --check` and `python3 tools/build.py`. Both must pass.
- Check the diff for personal information the owner has not approved (see `publishing.md`).

## Pull requests

- Title and description in English.
- For any visible change, attach before and after screenshots (at least the Japanese page and one right-to-left page such as Arabic).
- Watch CI on the pull request and fix failures until it passes. Do not skip or weaken a check to make it pass.
- The owner reviews and merges. Do not merge your own pull request.
