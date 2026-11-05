// Language menu.
// - Close the menu when the user clicks outside it.
// - Switching language replaces the current history entry instead of adding one,
//   so the browser's Back button goes to the page before, not to the previous language.
//   The target page is fetched and swapped in without a full reload; the address bar
//   still shows /<lang>/. If anything fails, the page is loaded with location.replace(),
//   which also adds no history entry. Without JavaScript the links work as normal links.
(function () {
  document.addEventListener('click', function (e) {
    var menu = document.querySelector('.langmenu');
    if (menu && !menu.contains(e.target)) menu.removeAttribute('open');
  });

  if (!window.fetch || !window.DOMParser || !history.replaceState) return;

  // Head elements that are the same on every page and must not be touched.
  function keep(el) {
    return el.matches('meta[charset], meta[http-equiv], meta[name="viewport"], meta[name="referrer"], link[rel="stylesheet"]');
  }

  function swap(html, url) {
    var doc = new DOMParser().parseFromString(html, 'text/html');
    var main = doc.querySelector('main');
    if (!main) throw new Error('no <main>');
    var root = document.documentElement;
    root.lang = doc.documentElement.lang;
    root.dir = doc.documentElement.dir;
    var head = document.head;
    Array.prototype.slice.call(head.children).forEach(function (el) { if (!keep(el)) head.removeChild(el); });
    Array.prototype.slice.call(doc.head.children).forEach(function (el) { if (!keep(el)) head.appendChild(document.importNode(el, true)); });
    document.querySelector('main').replaceWith(document.importNode(main, true));
    history.replaceState(history.state, '', url);
    document.dispatchEvent(new CustomEvent('langswitch'));
    var summary = document.querySelector('.langmenu > summary');
    if (summary) summary.focus();
  }

  var busy = false;
  document.addEventListener('click', function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target.closest ? e.target.closest('.langmenu a[hreflang]') : null;
    if (!a || a.origin !== location.origin) return;
    e.preventDefault();
    if (busy) return;
    busy = true;
    var url = a.href;
    fetch(url, { credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (html) { swap(html, url); busy = false; })
      .catch(function () { location.replace(url); });
  });
})();
