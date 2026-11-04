// 言語メニュー: メニューの外をクリックしたら閉じる
(function () {
  var menu = document.querySelector('.langmenu');
  if (!menu) return;
  document.addEventListener('click', function (e) {
    if (!menu.contains(e.target)) menu.removeAttribute('open');
  });
})();
