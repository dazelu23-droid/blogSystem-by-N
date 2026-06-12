(function () {
  const THEME_KEY = "blog-theme";
  const FONT_KEY = "blog-font";

  const THEMES = ["light", "dark", "ocean", "forest", "sunset", "lavender", "midnight"];
  const FONTS = ["system", "serif", "mono", "rounded", "elegant", "classic"];

  const themeToggle = document.getElementById("theme-toggle");
  const themeMenu = document.getElementById("theme-menu");
  const fontToggle = document.getElementById("font-toggle");
  const fontMenu = document.getElementById("font-menu");

  function getPreferredTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored && THEMES.includes(stored)) return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function getPreferredFont() {
    const stored = localStorage.getItem(FONT_KEY);
    if (stored && FONTS.includes(stored)) return stored;
    return "system";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (themeMenu) {
      themeMenu.querySelectorAll("[role='option']").forEach(function (item) {
        item.setAttribute("aria-selected", item.dataset.theme === theme ? "true" : "false");
      });
    }
  }

  function applyFont(font) {
    document.documentElement.setAttribute("data-font", font);
    if (fontMenu) {
      fontMenu.querySelectorAll("[role='option']").forEach(function (item) {
        item.setAttribute("aria-selected", item.dataset.font === font ? "true" : "false");
      });
    }
  }

  function closeMenu(menu, trigger) {
    if (!menu || !trigger) return;
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  }

  function openMenu(menu, trigger) {
    if (!menu || !trigger) return;
    menu.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
  }

  function closeAllMenus() {
    closeMenu(themeMenu, themeToggle);
    closeMenu(fontMenu, fontToggle);
  }

  function setupDropdown(toggle, menu, onSelect) {
    if (!toggle || !menu) return;

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      const isOpen = !menu.hidden;
      closeAllMenus();
      if (!isOpen) openMenu(menu, toggle);
    });

    menu.addEventListener("click", function (event) {
      const option = event.target.closest("[role='option']");
      if (!option) return;
      onSelect(option);
      closeMenu(menu, toggle);
    });
  }

  applyTheme(getPreferredTheme());
  applyFont(getPreferredFont());

  setupDropdown(themeToggle, themeMenu, function (option) {
    const theme = option.dataset.theme;
    localStorage.setItem(THEME_KEY, theme);
    applyTheme(theme);
  });

  setupDropdown(fontToggle, fontMenu, function (option) {
    const font = option.dataset.font;
    localStorage.setItem(FONT_KEY, font);
    applyFont(font);
  });

  document.addEventListener("click", closeAllMenus);

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeAllMenus();
  });
})();
