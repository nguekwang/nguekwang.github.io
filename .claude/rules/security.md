# Security

The site must not be open to injection, and it collects nothing from visitors except GoatCounter page views and click events.

- Never turn off Jinja autoescape (`select_autoescape` in `tools/build.py`), and never mark data as safe to skip escaping.
- No inline scripts or inline event handlers (the JSON-LD `application/ld+json` data block is the only inline `<script>`). Scripts live in `static/` and load from the site itself.
- The Content-Security-Policy in `templates/` allows only the site itself and GoatCounter. Keep `default-src 'none'`, `form-action 'none'`, `base-uri 'none'` and `object-src 'none'`.
- No forms and no third-party relay services. Visitors contact the owner by `mailto:` only.
