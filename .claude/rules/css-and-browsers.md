---
paths:
  - "static/**"
  - "templates/**"
---

# CSS and browsers

The shared rule is `web-browsers.md` in the `research-aide` repository: Chromium, Firefox and WebKit (Safari), phone and desktop width, light and dark mode, and the CSS and script behaviour that differs between engines. Here:

- Check every language, including the right-to-left ones.
- Style lives only in `static/style.css` and `templates/` (see `static.md` and `templates.md`).
- The site uses its own check instead of the shared workflow, because it also checks the language menu: `.github/workflows/browsers.yml` runs `tools/browser_check.py` on every pull request that can change what visitors see. It opens every page in Chromium, Firefox and WebKit at desktop and phone width, in light and dark mode, and fails on sideways scrolling, a language menu outside the window, or a JavaScript or console error (including Content-Security-Policy errors). Fix the CSS or template; do not loosen the check.
- For a visible change, also look at the `compare-*.png` images in the `browsers` workflow's artifact (the three engines side by side) and mention any difference between engines in the pull request description.
- Locally: `pip install -r requirements-browsers.txt`, `python3 -m playwright install chromium firefox webkit`, build, then `python3 tools/browser_check.py`.
