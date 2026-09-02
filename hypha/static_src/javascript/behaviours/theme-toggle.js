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
 * Persist the theme preference, ignoring unavailable storage.
 *
 * @param {string} mode - "light", "dark" or "auto".
 * @returns {boolean} Whether the preference could be stored.
 */
function storeTheme(mode) {
  try {
    localStorage.setItem("theme", mode);
    return true;
  } catch (_e) {
    return false;
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
  const currentTheme = getStoredTheme() || "auto";

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

function setupTheme() {
  // Attach event handlers for toggling themes
  let buttons = document.getElementsByClassName("theme-toggle");
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener("click", cycleTheme);
  }
}

initTheme();

document.addEventListener("DOMContentLoaded", function () {
  setupTheme();
});

// reset theme and release image if auto mode activated and os preferences have changed
window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", function (e) {
    prefersDark = e.matches;
    initTheme();
  });
