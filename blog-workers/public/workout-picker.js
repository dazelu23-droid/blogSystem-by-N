(function () {
  const openBtn = document.getElementById("workout-picker-open");
  const modal = document.getElementById("workout-picker");
  const closeBtn = document.getElementById("workout-picker-close");
  const backdrop = modal && modal.querySelector(".workout-modal-backdrop");

  if (!openBtn || !modal) return;

  function openModal() {
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    closeBtn.focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
    openBtn.focus();
  }

  openBtn.addEventListener("click", openModal);
  closeBtn.addEventListener("click", closeModal);
  if (backdrop) backdrop.addEventListener("click", closeModal);

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !modal.hidden) closeModal();
  });
})();
