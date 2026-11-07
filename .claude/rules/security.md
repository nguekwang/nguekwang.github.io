# Security

The shared rules are `security-first.md` and `web-security.md` in the `research-aide` repository. Here:

## What the site has

- Autoescape is `select_autoescape` in `tools/build.py`; never turn it off.
- The Content-Security-Policy and the referrer policy are built once, by `security_policies()` in `tools/security_policy.py`, and written right after `<meta charset>` by `templates/security.html.j2`, which every page template and `templates/cv.html.j2` include. Three kinds:
  - `measured` (every language page and sub-page): only the site itself and GoatCounter (script `GOATCOUNTER_SCRIPT`, counter origin from `goatcounter` in `data/site.yaml`); referrer `strict-origin-when-cross-origin`, because GoatCounter needs the page's origin.
  - `plain` (the language chooser at `/`): only the site's own redirect script, `connect-src 'none'`, referrer `no-referrer`.
  - `cv` (the CV HTML printed to PDF, never published): its own stylesheet `templates/cv.css` only, no scripts.
  - All three keep `default-src 'none'`, `form-action 'none'` (the site has no forms), `base-uri 'none'` and `object-src 'none'`, and allow no `'unsafe-inline'`, `'unsafe-eval'`, `data:` or wildcard. No `upgrade-insecure-requests` (shared rule: it adds nothing without `http:` sources and breaks the WebKit check on `http://127.0.0.1`).
- No `<style>` elements or `style=` attributes anywhere, the CV included; style lives in `static/style.css` (pages) and `templates/cv.css` (CV).
- `tools/security_check.py` (CI, `site.yml`, every pull request) checks every built page: policies in the right place and equal to `security_policies()`, the policies themselves, no inline style, inline script (other than JSON-LD) or event handler, no `javascript:` or `http://` URLs, scripts only from the site and GoatCounter, no forms, frames or objects, and `rel="noopener noreferrer"` on every new-tab link. `tools/build.py` runs the same check on each CV before printing it.
- The site collects nothing from visitors except GoatCounter page views and click events (see `measurement.md`).
- Settings > Pages > "Enforce HTTPS" stays on (the owner checks it; it cannot be read from a session).

## What the site cannot have yet (GitHub Pages sends no custom headers)

Waiting for a host that can send response headers (see `web-security.md` for the values):

- Content-Security-Policy as a header, with `frame-ancestors 'none'` (ignored in `<meta>`), so other sites cannot frame the pages (clickjacking).
- `X-Frame-Options: DENY` (same purpose, older browsers).
- `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` (whatever GitHub Pages sends for `github.io` is outside the site's control).
- `X-Content-Type-Options: nosniff` (same).
- `Referrer-Policy` as a header (the `<meta name="referrer">` above covers it for now).
- `Permissions-Policy` turning off camera, microphone, geolocation, payment, USB and every other feature the site does not use.
- `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Resource-Policy: same-origin`.
- CSP reporting (`report-to`), ignored in `<meta>`.

Not yet for another reason:

- Trusted Types (`require-trusted-types-for 'script'`): `static/lang.js` parses the fetched page with `DOMParser`, which Trusted Types blocks unless the script first defines a policy. Add both together, then add the directive to `security_policies()`.
