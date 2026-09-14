(function () {
  const group = document.querySelector("[data-compare-limit]");
  if (!group) return;

  const max = Number(group.getAttribute("data-compare-limit") || 0);
  if (!max) return;

  const boxes = Array.from(group.querySelectorAll('input[type="checkbox"]'));

  function sync() {
    const chosen = boxes.filter((box) => box.checked).length;
    boxes.forEach((box) => {
      box.disabled = !box.checked && chosen >= max;
      box.closest(".compare-option")?.classList.toggle("is-disabled", box.disabled);
    });
  }

  boxes.forEach((box) => box.addEventListener("change", sync));
  sync();
})();
