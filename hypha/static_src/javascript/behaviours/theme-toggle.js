let prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

function setTheme(mode) {
  if (mode !== "light" && mode !== "dark" && mode !== "auto") {
    console.error(`Got invalid theme mode: ${mode}. Resetting to auto.`);
    mode = "auto";
  }
  document.documentElement.dataset.theme = mode;
  localStorage.setItem("theme", mode);
}

function cycleTheme() {
  const currentTheme = localStorage.getItem("theme") || "auto";

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
  const currentTheme = localStorage.getItem("theme");
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
