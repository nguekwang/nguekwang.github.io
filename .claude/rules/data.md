---
paths:
  - "data/**"
---

# Data (`data/`)

All page text lives here as YAML. HTML structure is in `templates/`.

- `data/site.yaml`: site-wide settings, names, language order (`languages`), keyword groups and their order (`keywords`). Page titles are `<name> – <site_title>` (built by `site_title()` in `tools/build.py`): `site_title` is page text in each language file, and the name is `name.ja` on Japanese pages and `name.latin_title` (surname first, the owner's choice) elsewhere.
- `data/i18n/<code>.yaml`: all page text for one language.
- `data/talks.yaml`: talks (language-independent).
- `data/publications.yaml`: publications and theses (see below).
- `data/institutions.yaml`: institution names per language (official or translated).
- `data/post_editors.yaml`: native speakers who post-edited a machine-translated language (see `writing-style.md`).
- `data/privacy.yaml`: allow list for `tools/privacy_check.py` (see `build-and-ci.md`).
- `data/ai_tools.yaml`: services that read a project's GitHub repository, and each project's public repository (see below).

## Every language has the same items

- The site's languages are the ones listed under `languages` in `data/site.yaml`. Apply every change to all of them, not only to Japanese or English.
- Every language file must have exactly the same keys, list lengths and keyword ids as `en.yaml`. Only `mt_notice` may be empty (see `writing-style.md`).
- When adding a key or a list item, add it to every language file in the same change. `python3 tools/build.py --check` (and CI) fails otherwise. Fix the data; never add a fallback.
- Do not hard-code the number of languages anywhere; it grows when someone requests a new translation.
- To add a language: copy `data/i18n/en.yaml` to `data/i18n/<code>.yaml`, translate every value, and add the code to `languages`.

## Keywords

- Keywords are shown in groups. `keywords` in `data/site.yaml` lists the groups in display order, each with a `group` id and its keyword ids (`items`).
- Every language file has a label for each group under `keyword_groups` and a translation for each keyword under `keywords`. A keyword belongs to exactly one group.
- Keep the groups in line with the research text (`interests`, `current`): language comparison first, then theoretical linguistics (including analytic philosophy, at the owner's request), objects of study, mathematics and data, and technology (the last two next to each other). Group labels name fields at the same level; do not use a label (such as "research areas") that covers the other groups.
- Do not list keywords whose fields overlap as separate items: merge them into one (for example "Probability theory and statistics"), and do not repeat a group label as a keyword.

## Projects and their links for AI assistants

- Each project with a public repository gets a page of links for AI assistants at `/<lang>/ai-tools/<repo name>/`, linked under the project in the Projects section. It lists services that read the repository when `github.com` in its URL is replaced (`services` in `data/ai_tools.yaml`), each with its URL and a description (`ai_tools_desc` in every language file).
- The page heading and the link to it (`ai_tools_h`, with `{project}` exactly once) say that the repository is read with external AI services, so the project itself does not look like an AI tool (the owner's request). Do not put the project name before a colon and a generic label such as "Links for AI assistants".
- Every time a project is added to `projects` in the language files, add it under `projects` in `data/ai_tools.yaml` in the same change; `python3 tools/build.py --check` fails otherwise. Set `repo` (owner/name) as soon as the repository is public, even before it has code (the owner's choice); while it is private or missing, leave it empty, which shows no link and builds no page. Never set a private repository.
- When a project runs somewhere (for example Languer Map at `https://nguekwang.github.io/languer/`, a GitHub Pages project site from its own repository), set `site` for it in `data/ai_tools.yaml`; its name in the Projects section, the CV and `llms.txt` then links there. Host project sites as GitHub Pages project sites under `https://nguekwang.github.io/<repository name>/` (github.io gives no sub-subdomains), and do not create a directory with the same name in this site.
- Before adding a service, check that it is running and that it works by replacing `github.com`; record the date checked in `data/ai_tools.yaml`. Remove a service that has shut down. A new service needs a description in every language file in the same change.

## Values that are not page text

- `updated` in each language file is only a label with one `{date}` placeholder. The date comes from git (see `build-and-ci.md`); never write a date in the YAML.
- `same_as` in `data/site.yaml` lists the owner's other profiles for the JSON-LD (GitHub now; add ORCID and researchmap when they exist).
- `verification` in `data/site.yaml` holds the Google Search Console and Bing Webmaster Tools tokens (HTML meta tag method).

## Publications

- Every publication or thesis is one entry in `data/publications.yaml`, newest first. Never write one into a template or a language file. The build lists every entry on every language page, in the CV and in `llms.txt`.
- Each entry has the title as written (`title`, `lang`), the English title (`title_en`, required when the title is not English), `year`, `type` and optional `status`. Every language shows both titles.
- A line reads `<title> (<English title>) (<year>) (<type>, <status>)`, as the owner asked, with no label in front; for example `言語間の類似度の定量的な算出（A Quantitative Analysis of Cross-Linguistic Similarity）（2026）（卒業論文、非公開）`.
- The brackets, comma and spacing come from `pub_title_en`, `pub_note` and `list_sep` in each language file, written as that language's modern official documents write them. The year uses the language's digits (`digits` in `data/site.yaml`).
- A new `type` or `status` needs a translation under `pub_types` or `pub_status` in every language file in the same change; `python3 tools/build.py --check` fails otherwise.

## Digits

Digits follow the language's modern official documents, like all other notation. Current choices and their basis:

- Persian (`fa`): Persian digits (۰-۹), as in Iranian government documents.
- Hindi (`hi`): 0-9. Article 343(1) of the Constitution of India makes "the international form of Indian numerals" (0-9) the form for the Union's official purposes.
- Arabic (`ar`): 0-9 (the owner's decision). Official documents differ by country (٠-٩ in parts of the Mashriq and the Gulf, 0-9 in the Maghreb); the site does not target one country, so it follows the United Nations' Arabic official documents, which use 0-9.
- Thai (`th`): Thai government documents use Thai digits (๐-๙). The page uses 0-9 until the owner decides whether to switch.
- Every other language: 0-9.
- To use other digits, write them in `data/i18n/<code>.yaml` and list the language under `digits` in `data/site.yaml` (used for the dates and years the build generates), and update the list above in the same change.
- Never convert digits in whole strings at build time: identifiers such as "i18n" must keep 0-9.
