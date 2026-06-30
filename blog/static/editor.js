(function () {
  const textarea = document.getElementById("body");
  const editorEl = document.getElementById("quill-editor");
  if (!textarea || !editorEl) return;

  if (typeof Quill === "undefined") {
    const wrap = editorEl.closest(".quill-editor-wrap");
    if (wrap) wrap.hidden = true;
    textarea.hidden = false;
    textarea.rows = 12;
    textarea.removeAttribute("maxlength");
    textarea.setAttribute("maxlength", "20000");
    const hint = document.querySelector(".editor-hint");
    if (hint) hint.textContent = "Rich editor failed to load — using plain text.";
    return;
  }

  const form = textarea.closest("form");
  const counter = document.getElementById("body-counter");
  const errorEl = document.getElementById("body-error");
  const MAX = 20000;

  const quill = new Quill("#quill-editor", {
    theme: "snow",
    placeholder: "Write your story — headings, lists, links, and more…",
    modules: {
      toolbar: [
        [{ header: [1, 2, 3, false] }],
        ["bold", "italic", "underline", "strike"],
        [{ list: "ordered" }, { list: "bullet" }],
        ["blockquote", "code-block"],
        ["link", "clean"],
      ],
    },
  });

  const initial = textarea.value.trim();
  if (initial) {
    quill.root.innerHTML = initial;
  }

  function textLength() {
    return Math.max(0, quill.getText().trim().length);
  }

  function showError(message) {
    if (!errorEl) return;
    errorEl.textContent = message;
    errorEl.hidden = !message;
    editorEl.closest(".quill-editor-wrap")?.classList.toggle("has-error", Boolean(message));
  }

  function updateCounter() {
    const len = textLength();
    if (counter) {
      counter.textContent = `${len.toLocaleString()} / ${MAX.toLocaleString()}`;
      counter.classList.toggle("char-counter--warn", len > MAX * 0.9 && len <= MAX);
      counter.classList.toggle("char-counter--over", len > MAX);
    }
  }

  quill.on("text-change", () => {
    showError("");
    updateCounter();
  });

  updateCounter();

  form?.addEventListener("submit", (event) => {
    const len = textLength();
    if (len === 0) {
      event.preventDefault();
      showError("Body cannot be empty.");
      quill.focus();
      return;
    }
    if (len > MAX) {
      event.preventDefault();
      showError(`Body must be at most ${MAX.toLocaleString()} characters.`);
      return;
    }
    textarea.value = quill.root.innerHTML;
  });
})();
