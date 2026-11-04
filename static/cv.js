// Conversion tracking for GoatCounter.
// - A click on a link with data-cv="<name>" is counted as the GoatCounter event "cv-<name>".
// - The campaign tag of the visit (?ref=card, ?ref=github, ...) is sent as the event's referrer,
//   so conversions can be split by traffic source in the dashboard.
// - The language menu links keep ?ref=, so switching language does not lose the traffic source.
// - A language switch done by lang.js without a reload is counted as a page view of the new language.
// No cookies or local storage are used; nothing is sent when GoatCounter is blocked.
(function () {
  var ref = new URLSearchParams(location.search).get('ref');

  function keepRef() {
    if (!ref) return;
    var links = document.querySelectorAll('.langmenu a[hreflang]');
    for (var i = 0; i < links.length; i++) {
      links[i].href = links[i].getAttribute('href') + '?ref=' + encodeURIComponent(ref);
    }
  }
  keepRef();

  // lang.js swapped in another language version without a reload (see static/lang.js):
  // tag the new menu links again and count the new page as a page view.
  document.addEventListener('langswitch', function () {
    keepRef();
    if (window.goatcounter && window.goatcounter.count) {
      var vars = { path: location.pathname, title: document.title };
      if (ref) vars.referrer = ref;
      window.goatcounter.count(vars);
    }
  });

  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[data-cv]') : null;
    if (!a || !window.goatcounter || !window.goatcounter.count) return;
    var vars = {
      path: 'cv-' + a.getAttribute('data-cv'),
      title: a.getAttribute('data-cv') + ' (' + document.documentElement.lang + ')',
      event: true
    };
    if (ref) vars.referrer = ref;
    window.goatcounter.count(vars);
  });
})();
