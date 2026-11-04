---
paths:
  - "data/**"
---

# Writing the page text

## Wording
- Headings, buttons and menu items are noun phrases, not sentences or commands.
- Use the formal wording a researcher's page would use (for example "Research topics", not "Research interests").
- Language skills are given as CEFR levels only (for example English C1, Spanish B1, Japanese native). Do not name the exam.
- Keep the owner's names as they are in `name` in `data/site.yaml` (`Yoshihiro (Yoshi) MATSUURA`, `松浦 義広`). The only nickname is `Yoshi`. Do not change them without the owner's request.

## Projects
- Services and apps get display names in title case with spaces (`Corpus Hub`, `Languer Map`). Command-line tools and libraries keep lowercase kebab-case names (`linguasim`, `syntax-tree`). A kebab-case service name is used only for its repository and URL.
- A project's name is spelled the same in every language; only its description is translated.
- Every description states the project's status (in development, planned, ...).
- List only projects the owner asked to list, and never link to a private repository.

## Institution names
- For each language, use the name the institution itself publishes in that language if there is one (official); otherwise translate its meaning (translated).
- Record which one, with its source, in `data/institutions.yaml`. The institution names page shows this status for every language.

## Machine translation notice
- `mt_notice` is empty only for the languages the owner wrote (`en`, `ja`, `es`). Every other language must show the notice.
