# Instruction files

Rules for the files Claude reads as instructions: `CLAUDE.md` and everything in `.claude/` (rules, skills, settings). Apply them whenever you add, change or move an instruction.

## What goes where

- `CLAUDE.md`: what this repository is, the principles behind the rules, and a map of the rule files. No commands, file-by-file details or one-off decisions. Keep it under about 40 lines.
- `.claude/rules/<topic>.md` without `paths`: rules that apply to every task wherever Claude works (how to talk to the owner, git, language, privacy). Claude Code loads these at the start of every session.
- `.claude/rules/<topic>.md` with `paths`: rules about one directory or one kind of file. Claude Code loads them only when Claude reads or edits a matching file, so they cost nothing in other tasks. Name the file after the directory (`data.md`, `templates.md`), or after the topic when it spans several directories (`measurement.md`).
- `.claude/skills/<name>/SKILL.md`: a procedure of several steps that is only needed for some tasks.
- Values a program reads (settings, lists, numbers) go in the data or config files, not in prose. A rule file may point to them.

## Path-scoped rules

```markdown
---
paths:
  - "data/**"
---
```

- `paths` is the only frontmatter field Claude Code reads. Patterns are globs relative to the repository root.
- A path-scoped rule is not loaded until a matching file is opened. If Claude must know a rule before it touches any file (for example, before planning), the rule belongs in an always-loaded file instead.

## How to write them

- One topic per file. Each rule is stated in one place only; elsewhere, point to it instead of repeating it.
- English, short imperative bullets. Add the reason when it is not obvious.
- Name real files, keys and commands so the rule can be checked against the code. When the code changes, update the rule in the same pull request.
- No private information: this repository is public (see `publishing.md`).
- Split a rule file when it grows past about 60 lines.
- When adding, renaming or removing a rule file, update the map in `CLAUDE.md`.
