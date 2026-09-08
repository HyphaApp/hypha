(function () {
  let prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

  /**
   * Read the stored theme preference.
   *
   * Storage can be unavailable (blocked cookies, some private browsing modes)
   * and then throws. This script runs blocking in <head>, so an uncaught error
   * would leave the page with no theme applied at all.
   *
   * @returns {string|null} "light", "dark", "auto", or null if nothing is stored.
   */
  function getStoredTheme() {
    try {
      return localStorage.getItem("theme");
    } catch (_e) {
      return null;
    }
  }

  /**
   * Read the theme currently applied to the document.
   *
   * The DOM is authoritative here rather than localStorage, which can be
   * unavailable and would then report "auto" on every click, leaving the toggle
   * stuck on a single theme.
   *
   * @returns {string} "light", "dark" or "auto".
   */
  function getCurrentTheme() {
    return document.documentElement.dataset.theme || "auto";
  }

  /**
   * Persist the theme preference, ignoring unavailable storage.
   *
   * @param {string} mode - "light", "dark" or "auto".
   */
  function storeTheme(mode) {
    try {
      localStorage.setItem("theme", mode);
    } catch (_e) {
      // Nothing to do: the theme still applies for this page view.
    }
  }

  function setTheme(mode) {
    if (mode !== "light" && mode !== "dark" && mode !== "auto") {
      console.error(`Got invalid theme mode: ${mode}. Resetting to auto.`);
      mode = "auto";
    }

    // daisyUI applies the dark theme through `:root:not([data-theme])` inside a
    // prefers-color-scheme media query, so auto mode has to leave the attribute
    // off entirely. Setting data-theme="auto" matches no theme and silently
    // falls back to light.
    if (mode === "auto") {
      delete document.documentElement.dataset.theme;
    } else {
      document.documentElement.dataset.theme = mode;
    }

    storeTheme(mode);
  }

  function cycleTheme() {
    const currentTheme = getCurrentTheme();

    if (prefersDark) {
      // Auto (dark) -> Light -> Dark
      if (currentTheme === "auto") {
        setTheme("light");
      } else if (currentTheme === "light") {
        setTheme("dark");
      } else {
        setTheme("auto");
      }
    } else {
      // Auto (light) -> Dark -> Light
      if (currentTheme === "auto") {
        setTheme("dark");
      } else if (currentTheme === "dark") {
        setTheme("light");
      } else {
        setTheme("auto");
      }
    }
  }

  function initTheme() {
    // set theme defined in localStorage if there is one, or fallback to auto mode
    const currentTheme = getStoredTheme();
    currentTheme ? setTheme(currentTheme) : setTheme("auto");
  }

  initTheme();

  // Delegated so the toggle keeps working after htmx swaps the header out, which
  // hx-boost links without an hx-target do by replacing the whole <body>.
  // It sees every click on the page, so closest() is guarded: a click event
  // can be dispatched at a non-Element target, which has no closest().
  document.addEventListener("click", function (e) {
    if (e.target.closest?.(".theme-toggle")) {
      cycleTheme();
    }
  });

  // Auto mode carries no data-theme attribute, so the CSS follows the OS on its
  // own and nothing needs re-applying when the OS preference changes. Only the
  // order the toggle cycles through depends on it.
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", function (e) {
      prefersDark = e.matches;
    });
})();
