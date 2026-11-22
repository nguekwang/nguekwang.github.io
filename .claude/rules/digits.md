---
paths:
  - "data/**"
---

# Digits

Digits follow the language's modern official documents, like all other notation. Current choices and their basis:

- Persian (`fa`): Persian digits (۰-۹), as in Iranian government documents.
- Hindi (`hi`): 0-9. Article 343(1) of the Constitution of India makes "the international form of Indian numerals" (0-9) the form for the Union's official purposes.
- Arabic (`ar`): 0-9 (the owner's decision). Official documents differ by country (٠-٩ in parts of the Mashriq and the Gulf, 0-9 in the Maghreb); the site does not target one country, so it follows the United Nations' Arabic official documents, which use 0-9.
- Thai (`th`): Thai government documents use Thai digits (๐-๙). The page uses 0-9 until the owner decides whether to switch.
- Every other language: 0-9.
- To use other digits, write them in `data/i18n/<code>.yaml` and list the language under `digits` in `data/site.yaml` (used for the dates and years the build generates), and update the list above in the same change.
- Never convert digits in whole strings at build time: identifiers such as "i18n" must keep 0-9.
