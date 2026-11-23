// ESLint settings (flat config) for the JavaScript in this repository; see
// .claude/rules/build-and-ci.md. Only the recommended rules, which find likely errors; layout is
// left to Prettier.
import js from '@eslint/js';
import globals from 'globals';

export default [
  {
    ignores: ['_site/', '_preview/', 'browser-check/'],
  },
  js.configs.recommended,
  {
    // Classic scripts the pages load with <script src>, in the browser.
    files: ['static/**/*.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'script',
      globals: { ...globals.browser },
    },
  },
  {
    files: ['*.mjs'],
    languageOptions: {
      sourceType: 'module',
      globals: { ...globals.node },
    },
  },
];
