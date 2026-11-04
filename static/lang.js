// Language menu: close it when the user clicks outside the menu
(function () {
  var menu = document.querySelector('.langmenu');
  if (!menu) return;
  document.addEventListener('click', function (e) {
    if (!menu.contains(e.target)) menu.removeAttribute('open');
  });
})();
