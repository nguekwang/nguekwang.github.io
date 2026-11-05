---
paths:
  - "templates/**"
---

# Templates (`templates/`)

HTML structure only. Page text comes from `data/`; never write page text into a template.

- Fix layout once here (or in `static/style.css`). Never special-case a single page, language or link.
- Do not write `target` or `rel` on links. The build adds `target="_blank" rel="noopener noreferrer"` to every `http(s)` link outside `site.url` (`open_external_in_new_tab()` in `tools/build.py`). `mailto:` links, in-page anchors and links between the site's own pages (such as the language menu) stay in the same tab.
- The language menu uses ordinary links to each `/<lang>/` page; `static/lang.js` enhances them (see `static.md`). Pages that load it need `connect-src 'self'` in their Content-Security-Policy.
- Page order: the first screen has the name, a one-line research summary, the email and GitHub buttons, and the talks carousel when there are talks. Below it: research topics, keywords, current research, publications and talks, projects, background, languages, contact. Change the order only at the owner's request. Do not move the graduation line back to the top.
- The translation request is the last item of the language menu: a `mailto:` link whose subject and body come from `translation_request` in `data/site.yaml` (English noun phrases).
- Sub-pages under `/<lang>/` (`names.html.j2`, `ai_tools.html.j2`) extend `templates/subpage.html.j2`, which holds their head, language menu, back link and footer. Change that layout once there.
- `templates/llms.txt.j2` builds `_site/llms.txt`, a plain-text English summary for AI assistants, from `data/i18n/en.yaml`.
