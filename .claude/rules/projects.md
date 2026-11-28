---
paths:
  - "data/**"
---

# Projects and their links for AI assistants

- Each project with a public repository gets a page of links for AI assistants at `/<lang>/ai-tools/<repo name>/`, linked under the project in the Projects section. It lists services that read the repository (`services` in `data/ai_tools.yaml`). Each item leads with what it is for (`ai_tools_purpose`, which is the link), then a description (`ai_tools_desc`), then the service name as a small label (`ai_tools_service`). Do not print the service URLs or tell readers to replace `github.com` in the URL (no `github.com → host` lines); the owner found them unhelpful.
- The page heading and the link to it (`ai_tools_h`, with `{project}` exactly once) say that the repository is read with external AI services, so the project itself does not look like an AI tool (the owner's request). Do not put the project name before a colon and a generic label such as "Links for AI assistants".
- Every time a project is added to `projects` in the language files, add it under `projects` in `data/ai_tools.yaml` in the same change; `python3 tools/build.py --check` fails otherwise. Set `repo` (owner/name) as soon as the repository is public, even before it has code (the owner's choice); while it is private or missing, leave it empty, which shows no link and builds no page. Never set a private repository.
- When a project runs somewhere (for example Lang Log at `https://lang-log.com/`, the GitHub Pages site of its own organization on a custom domain), set `site` for it in `data/ai_tools.yaml`; its name in the Projects section, the CV and `llms.txt` then links there. A project site under `https://nguekwang.github.io/<repository name>/` is also possible; then do not create a directory with the same name in this site.
- Before adding a service, check that it is running and that it works by replacing `github.com`; record the date checked in `data/ai_tools.yaml`. Remove a service that has shut down. A new service needs a purpose and a description in every language file in the same change.
