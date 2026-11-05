---
paths:
  - "static/**"
  - "templates/**"
---

# CSS and browsers

The site must look and work the same in every browser and on every device the owner's visitors
use. In practice that means three browser engines:

- Chromium (Chrome, Edge, Opera, most Android browsers),
- Firefox (Gecko),
- WebKit (Safari on Mac, and every browser on iPhone and iPad).

Each at phone width (390 px) and desktop width, in light and dark mode, in every language
including right-to-left ones.

## Writing CSS

- Use only CSS that all three engines support in their current release (check MDN's
  compatibility table or caniuse.com). Do not rely on Chromium-only behaviour.
- A newer feature that one engine lacks (for example `text-box`, which Firefox does not support)
  is allowed only inside `@supports (...)`, and the page must look right without it. Put the
  plain rule first and the enhancement in the `@supports` block.
- For a new unit or value, write the widely supported value first and the new one second, so
  older browsers keep the first (e.g. `max-height: 70vh; max-height: 70dvh;`).
- Write the standard property next to any `-webkit-` prefixed one, and never use a prefixed
  property alone.
- Long words and URLs must wrap, never widen the page (`overflow-wrap` on `body`).
- Keep `color-scheme: light dark` on `:root`, so each engine draws its own scroll bars and
  controls in the right colours.
- Follow `.claude/rules/content-and-layout.md`: fix it once in `static/style.css` or `templates/`.

## Checking

- CI (`.github/workflows/browsers.yml`) runs `tools/browser_check.py` on every pull request:
  every page in Chromium, Firefox and WebKit at desktop and phone width. It fails on sideways
  scrolling, a language menu outside the window, or a JavaScript or console error (including
  Content-Security-Policy errors). Fix the CSS or template; do not loosen the check.
- For a visible change, also look at the `compare-*.png` images in the `browsers` workflow's
  artifact (the three engines side by side) and mention any difference between engines in the
  pull request description.
- Locally: `pip install -r requirements-browsers.txt`, `python3 -m playwright install chromium
  firefox webkit`, build, then `python3 tools/browser_check.py`.
