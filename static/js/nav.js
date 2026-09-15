(function () {
  const menus = Array.from(document.querySelectorAll("[data-nav-menu]"));
  if (!menus.length) {
    return;
  }

  function closeAll(except) {
    menus.forEach(function (menu) {
      if (menu !== except && menu.open) {
        menu.removeAttribute("open");
      }
    });
  }

  menus.forEach(function (menu) {
    menu.addEventListener("toggle", function () {
      if (menu.open) {
        closeAll(menu);
      }
    });
  });

  document.addEventListener("pointerdown", function (event) {
    if (!event.target.closest("[data-nav-menu]")) {
      closeAll();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeAll();
    }
  });

  window.addEventListener("resize", function () {
    if (window.innerWidth > 980) {
      closeAll();
    }
  });
})();
