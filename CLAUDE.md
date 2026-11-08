# CLAUDE.md

@../research-aide/.claude/common.md

The personal website of Matsuura Yoshihiro (https://nguekwang.github.io/): page text kept as YAML data in many languages, built into static HTML by `tools/build.py`, checked and deployed by GitHub Actions.

This file holds only the principles. The owner's shared rules come from the `research-aide` repository (imported above; clone it next to this repository). Rules only for this repository live in `.claude/rules/` (see the map below); they add site details to the shared rules.

If the shared rules are not in your context (the import above can be skipped, for example before external imports are approved or when `../research-aide` is missing), read `../research-aide/.claude/common.md` and every file it lists before doing anything else. If `../research-aide` does not exist, clone `nguekwang/research-aide` next to this repository first, or tell the owner.

## Principles

- **Publish only what the owner approved.** This repository and the site are public.
- **Every language shows the same thing**, and each language follows its own official documents (`languages.md` in `research-aide`).
- **Fix things once, at the source.** Text in `data/`, structure in `templates/`, style and scripts in `static/`, build logic in `tools/`. Never patch one page, one language or one link.
- **Plain pages that work for everyone.** Each language is its own static page with ordinary links, readable without JavaScript and by search engines and AI assistants, in every browser (`web-browsers.md` in `research-aide`).

## Where the rules are

Loaded in every session (each adds site details to the shared rule of the same topic):

- `.claude/rules/git-and-prs.md`: checks before pushing, screenshots and previews on pull requests.
- `.claude/rules/english-first.md`: where Japanese may appear.
- `.claude/rules/publishing.md`: what may be published and what stays out of this repository.
- `.claude/rules/security.md`: autoescape, Content-Security-Policy, measurement.

Loaded when Claude works on matching files:

- `.claude/rules/data.md`: `data/**`
- `.claude/rules/writing-style.md`: `data/**` (wording, project names, institution names, machine translation)
- `.claude/rules/templates.md`: `templates/**`
- `.claude/rules/static.md`: `static/**`
- `.claude/rules/css-and-browsers.md`: `static/**`, `templates/**` (CSS that works in Chromium, Firefox and WebKit/Safari)
- `.claude/rules/build-and-ci.md`: `tools/**`, `.github/**`, `requirements*.txt`, `lychee.toml` (build, CI and automated checks)
- `.claude/rules/measurement.md`: `data/site.yaml`, `templates/page.html.j2`, `static/cv.js`
