/**
 * Theme bootstrap. Loaded synchronously in <head> so the correct palette is
 * applied before first paint.
 *
 * Stored value: "light" | "dark". With no stored value, follow the OS and keep
 * following it until the user makes an explicit choice.
 */

(() => {
  const STORAGE_KEY = "trackit-theme";
  const root = document.documentElement;
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function stored() {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return value === "light" || value === "dark" ? value : null;
    } catch {
      return null;
    }
  }

  function apply(theme) {
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    for (const button of document.querySelectorAll("[data-theme-toggle]")) {
      button.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      );
      button.setAttribute("title", theme === "dark" ? "Light mode" : "Dark mode");
      const icon = button.querySelector(".theme-icon");
      if (icon) icon.textContent = theme === "dark" ? "☀" : "☾";
    }
  }

  function preferred() {
    return stored() || (media.matches ? "dark" : "light");
  }

  apply(preferred());

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-theme-toggle]");
    if (!button) return;
    const next = root.dataset.theme === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Private mode: still switch for this page.
    }
    apply(next);
  });

  media.addEventListener("change", () => {
    if (!stored()) apply(media.matches ? "dark" : "light");
  });

  document.addEventListener("DOMContentLoaded", () => apply(preferred()));
})();
