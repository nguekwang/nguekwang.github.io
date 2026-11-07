# Security

The shared rule is `web-security.md` in the `research-aide` repository. Here:

- Autoescape is `select_autoescape` in `tools/build.py`; never turn it off.
- The Content-Security-Policy is written in `templates/` and allows only the site itself and GoatCounter, with `form-action 'none'`. The site has no forms.
- The site collects nothing from visitors except GoatCounter page views and click events (see `measurement.md`).
