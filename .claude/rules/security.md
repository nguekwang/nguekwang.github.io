# Security

The shared rule is `web-security.md` in the `research-aide` repository. Here:

- Autoescape is `select_autoescape` in `tools/build.py`; never turn it off.
- The Content-Security-Policy is written once, in `templates/csp.html.j2` (included by `page.html.j2` and `subpage.html.j2`), and allows only the site itself and GoatCounter, with `form-action 'none'`. The GoatCounter origin is filled in from `goatcounter` in `data/site.yaml`. The site has no forms.
- The site collects nothing from visitors except GoatCounter page views and click events (see `measurement.md`).
