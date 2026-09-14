(function () {
  function items(root) {
    return Array.from(root.querySelectorAll(".suggest-item"));
  }

  function setActive(links, index) {
    links.forEach(function (link, i) {
      link.classList.toggle("is-active", i === index);
      if (i === index) {
        link.setAttribute("aria-selected", "true");
        link.scrollIntoView({ block: "nearest" });
      } else {
        link.removeAttribute("aria-selected");
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    const root = event.target.closest("[data-search-root]");
    if (!root) {
      return;
    }
    const links = items(root);
    if (event.key === "Escape") {
      const panel = root.querySelector("[data-search-panel]");
      if (panel) {
        panel.innerHTML = "";
      }
      return;
    }
    if (!links.length) {
      return;
    }
    const current = links.findIndex(function (link) {
      return link.classList.contains("is-active");
    });
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive(links, current < links.length - 1 ? current + 1 : 0);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive(links, current > 0 ? current - 1 : links.length - 1);
    } else if (event.key === "Enter" && current >= 0) {
      event.preventDefault();
      links[current].click();
    }
  });

  document.body.addEventListener("htmx:afterSwap", function (event) {
    const target = event.detail && event.detail.target;
    if (!target || !target.hasAttribute("data-search-panel")) {
      return;
    }
    const root = target.closest("[data-search-root]");
    const input = root && root.querySelector("input[type='search']");
    if (input) {
      input.setAttribute(
        "aria-expanded",
        target.querySelector("[role='listbox']") ? "true" : "false"
      );
    }
  });
})();
