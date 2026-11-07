---
paths:
  - "static/**"
---

# Static files (`static/`)

Copied to the site as they are (CSS, JS, robots.txt).

- `static/style.css` is the one place for style. Do not add per-page or per-language style rules.
- The CSS must work in Chromium, Firefox and WebKit (Safari): see `css-and-browsers.md`.
- Switching language must not add a browser history entry, so Back goes to the page before, not to the previous language. `static/lang.js` fetches the other language version and swaps it in with `history.replaceState()` (falling back to `location.replace()`); the URL still shows `/<lang>/`. Keep it an enhancement: the links must still work without JavaScript.
- Every script must work under the pages' Content-Security-Policy (`tools/security_policy.py`; see `security.md`). If a script needs a new source, change the policy there in the same pull request.
