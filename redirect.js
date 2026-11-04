// 言語の振り分け: ブラウザの言語設定に合う版(/<言語>/)へ移動する。合う版がなければ英語版。
// ?ref= などはそのまま引き継ぐ。外部サイトから来た場合は、元のサイト名を ref に入れて流入元が消えないようにする。
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
