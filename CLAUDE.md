# CLAUDE.md

The personal website of Matsuura Yoshihiro (https://nguekwang.github.io/): page text kept as YAML data in many languages, built into static HTML by `tools/build.py`, checked and deployed by GitHub Actions.

This file holds only the principles. Concrete rules live in `.claude/rules/` (see the map below).

## Principles

- **The owner decides and reviews.** Every change goes through a pull request; the owner merges. Earlier decisions are recorded in this repository; follow them, and when a request conflicts with one, say so instead of overriding it.
- **Publish only what the owner approved.** This repository and the site are public.
- **Every language shows the same thing.** A change is not done until every language has it.
- **Fix things once, at the source.** Text in `data/`, structure in `templates/`, style and scripts in `static/`, build logic in `tools/`. Never patch one page, one language or one link.
- **Plain pages that work for everyone.** Each language is its own static page with ordinary links, readable without JavaScript and by search engines and AI assistants.
- **English first.** The repository reads as English; other languages appear only as page content and names.
- **Each language follows its own official documents.** Digits, dates, punctuation and other notation follow the conventions of that language's current official documents (government, legislature, national standards), not one style shared by all languages.
- **Write decisions down.** When a new rule is decided, record it in the right rule file in the same pull request.

## Where the rules are

Loaded in every session:

- `.claude/rules/instruction-files.md`: how this file and the rule files are organized and written. Read it before editing any of them.
- `.claude/rules/working-with-the-owner.md`: starting a task, asking questions, reporting.
- `.claude/rules/git-and-prs.md`: branches, conflicts, checks, pull requests.
- `.claude/rules/english-first.md`: which language each part of the repository is written in.
- `.claude/rules/publishing.md`: what may be published and what stays out of this repository.
- `.claude/rules/security.md`: escaping, scripts, Content-Security-Policy, no forms.

Loaded when Claude works on matching files:

- `.claude/rules/data.md`: `data/**`
- `.claude/rules/writing-style.md`: `data/**` (wording, project names, institution names, machine translation and post-editors)
- `.claude/rules/templates.md`: `templates/**`
- `.claude/rules/static.md`: `static/**`
- `.claude/rules/css-and-browsers.md`: `static/**`, `templates/**` (CSS that works in Chromium, Firefox and WebKit/Safari)
- `.claude/rules/build-and-ci.md`: `tools/**`, `.github/**`, `requirements*.txt`, `lychee.toml` (build, CI and automated checks)
- `.claude/rules/measurement.md`: `data/site.yaml`, `templates/page.html.j2`, `static/cv.js`
