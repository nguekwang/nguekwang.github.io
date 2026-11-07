# What may be published

The shared rule is `publishing.md` in the `research-aide` repository. This repository and the site are public. Here:

- The birth month and year and home city in the background section were added at the owner's request; nothing else personal beyond what the site already shows.
- Data that must stay private, such as measurement results, the measurement plan and the list of initiatives (施策), is kept outside this repository.
- Do not add a `README.md`.
- The thesis is listed by title only. Do not publish its PDF.
- The email address is shown as plain text and a `mailto:` link, without obfuscation.
- Pull request previews at `/preview/pr-<number>/` are public too (with `noindex`). They are published only after the pull request passed `tools/privacy_check.py`, so the same check before pushing applies to every pull request, not only to what is merged.
