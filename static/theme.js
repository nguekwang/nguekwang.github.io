// Light/dark theme toggle (the round button next to the language menu).
// - Without a saved choice the page follows the system setting (prefers-color-scheme).
// - A click saves the other theme in localStorage and sets <html data-theme="light|dark">,
//   which style.css reads. The choice is per site, so it stays across language switches
//   and on every page.
// - This file is loaded in <head>, before the page is drawn, so a saved theme is applied
//   without a flash of the other one. lang.js keeps this script when it swaps pages.
// - Without JavaScript the button stays hidden and the page follows the system setting.
(function () {
  var root = document.documentElement;
  var KEY = 'theme';
  var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  function saved() {
    try { var v = localStorage.getItem(KEY); return v === 'light' || v === 'dark' ? v : null; }
    catch (e) { return null; }
  }
  function current() {
    return root.getAttribute('data-theme') || (media && media.matches ? 'dark' : 'light');
  }
  function sync() {
    var dark = current() === 'dark';
    Array.prototype.forEach.call(document.querySelectorAll('.theme-toggle'), function (b) {
      b.setAttribute('aria-pressed', dark ? 'true' : 'false');
    });
  }

  var s = saved();
  if (s) root.setAttribute('data-theme', s);
  root.setAttribute('data-theme-js', '');

  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('.theme-toggle') : null;
    if (!b) return;
    var next = current() === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem(KEY, next); } catch (e2) { /* private mode: keep for this page only */ }
    sync();
  });

  document.addEventListener('DOMContentLoaded', sync);
  document.addEventListener('langswitch', sync);
  if (media) {
    if (media.addEventListener) media.addEventListener('change', sync);
    else if (media.addListener) media.addListener(sync);
  }
})();
