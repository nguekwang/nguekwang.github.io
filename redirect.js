// Language redirect: go to the version (/<lang>/) that matches the browser language settings, or English if none matches.
// Query parameters such as ?ref= are kept. When the visitor comes from another site, its host name is put into ref so the traffic source is not lost.
(function () {
  var langs = document.currentScript.getAttribute('data-langs').split(' ');
  function pick(tag) {
    tag = tag.toLowerCase();
    if (tag.indexOf('zh') === 0) {
      return /hant|tw|hk|mo/.test(tag) ? 'zh-Hant' : 'zh-Hans';
    }
    var base = tag.split('-')[0];
    return langs.indexOf(base) >= 0 ? base : null;
  }
  var prefs = navigator.languages || [navigator.language || 'en'];
  var target = 'en';
  for (var i = 0; i < prefs.length; i++) { var l = pick(prefs[i]); if (l) { target = l; break; } }
  var params = new URLSearchParams(location.search);
  if (!params.has('ref') && document.referrer) {
    try {
      var host = new URL(document.referrer).hostname;
      if (host && host !== location.hostname) params.set('ref', host);
    } catch (e) {}
  }
  var q = params.toString();
  location.replace(target + '/' + (q ? '?' + q : '') + location.hash);
})();
