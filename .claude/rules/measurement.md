---
paths:
  - "data/site.yaml"
  - "templates/page.html.j2"
  - "static/cv.js"
---

# Measurement (GoatCounter)

- Page views are counted by GoatCounter (`goatcounter` in `data/site.yaml`). Links we share carry a campaign tag, e.g. `?ref=card` (business card QR) or `?ref=github`.
- Conversions are clicks on links marked with `data-cv="<name>"` in `templates/page.html.j2`. `static/cv.js` sends each one as the GoatCounter event `cv-<name>`, with the visit's `?ref=` as its referrer, and keeps `?ref=` on language menu links.
- `?ref=` values are lowercase, with `-` between words (`card`, `github`, `orcid`, `slides-<venue><year>`). Keep existing values as they are. For a new initiative, the owner records it in the measurement plan (outside this repository) before the tag is chosen.
- `pr-<number>` is reserved for pull request previews (`/preview/pr-<number>/`, linked on the pull request by `.github/workflows/pages.yml`). These visits are review traffic, not visitors: leave them out of results (filter by the `/preview/` path or the `pr-` ref).
- Current names: `email-top`, `email-contact`, `github-top`, `github-contact`, `cv-top` (the CV PDF button, event `cv-cv-top`), `talk`, `request-lang`, `project-site` (a project's own site, linked from its name in the Projects section). When adding a link to another profile (ORCID, researchmap), give it a `data-cv` name too.
- Results and plans stay outside this repository (see `publishing.md`).
