// Conversion tracking for GoatCounter.
// - A click on a link with data-cv="<name>" is counted as the GoatCounter event "cv-<name>".
// - The campaign tag of the visit (?ref=card, ?ref=github, ...) is sent as the event's referrer,
//   so conversions can be split by traffic source in the dashboard.
// - The language menu links keep ?ref=, so switching language does not lose the traffic source.
// No cookies or local storage are used; nothing is sent when GoatCounter is blocked.
(function () {
  var ref = new URLSearchParams(location.search).get('ref');

  if (ref) {
    var links = document.querySelectorAll('.langmenu a[hreflang]');
    for (var i = 0; i < links.length; i++) {
      links[i].href = links[i].getAttribute('href') + '?ref=' + encodeURIComponent(ref);
    }
  }

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
