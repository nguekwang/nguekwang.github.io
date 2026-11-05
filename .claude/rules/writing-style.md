---
paths:
  - "data/**"
---

# Writing the page text

## Wording
- Headings, buttons and menu items are noun phrases, not sentences or commands.
- Use the formal wording a researcher's page would use (for example "Research topics", not "Research interests").
- Language skills are given as CEFR levels only (for example English C1, Spanish B1, Japanese native). Do not name the exam.
- Keep the owner's names as they are in `name` in `data/site.yaml` (`Yoshihiro (Yoshi) MATSUURA`, `松浦 義広`, and `MATSUURA Yoshihiro` in page titles). The only nickname is `Yoshi`. Do not change them without the owner's request.

## Projects
- Services and apps get display names in title case with spaces (`Corpus Hub`, `Languer Map`). Command-line tools and libraries keep lowercase kebab-case names (`linguasim`, `syntax-tree`). A kebab-case service name is used only for its repository and URL.
- A project's name is spelled the same in every language; only its description is translated.
- Every description states the project's status (in development, planned, ...).
- List only projects the owner asked to list, and never link to a private repository.

## Institution names
- For each language, use the name the institution itself publishes in that language if there is one (official); otherwise translate its meaning (translated).
- Record which one, with its source, in `data/institutions.yaml`. The institution names page shows this status for every language.

## Machine translation and post-editors
- English, Japanese and Spanish are written by the owner; their `mt_notice` is empty. Every other language is machine-translated and must show `mt_notice`.
- A native speaker may post-edit (review and correct) a machine-translated language. List them in `data/post_editors.yaml`; that language's pages then show `post_edited` with their names instead of `mt_notice`.
- Add a person only after they agree to be named, with the name and the one link (social media, website or GitHub) they chose. Never commit their contact details; the build rejects any field other than `name` and `url`.
- Claude does not contact possible post-editors. Claude may draft the request; the owner sends it.
- Do not overwrite a post-edited language with a new machine translation of the whole file. Translate only the changed text and ask the owner to have the post-editor check it.
- `.github/workflows/post-editor-links.yml` checks the post-editors' links weekly and emails the owner through Gmail when one breaks. Never report these links in an issue, and keep names and URLs out of public workflow logs.
