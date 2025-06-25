/**
 * Cleans up and enhances content within containers using the "prose" class (excluding those with "not-prose"):
 *
 * 1. Paragraph Cleanup:
 *    - Removes <p> elements that are empty or contain only whitespace or invisible characters (e.g., zero-width spaces).
 *    - Ensures each <p> has dir="auto" to allow browsers to automatically determine text directionality (LTR or RTL).
 *
 * 2. Table Wrapping:
 *    - Wraps each <table> inside a <div class="table-container"> for improved styling and layout,
 *      unless the table is already wrapped in such a container.
 *
 * The function runs on DOMContentLoaded and after htmx content updates (if htmx is present).
 */
function proseCleanupAndTableWrap() {
  // Select all containers with class "prose" that do not also have "not-prose"
  const proseContainers = document.querySelectorAll(".prose:not(.not-prose)");
  proseContainers.forEach((container) => {
    // Use a static NodeList to avoid issues when removing elements during iteration.
    const paras = Array.from(container.querySelectorAll("p"));
    for (const para of paras) {
      // Remove <p> tags with only whitespace or invisible characters inside.
      if (
        !para.textContent ||
        para.textContent.replace(/\u200B/g, "").trim() === ""
      ) {
        para.remove();
        continue;
      }
      // Set dir="auto" so browsers set the correct directionality (ltr/rtl).
      if (para.getAttribute("dir") !== "auto") {
        para.setAttribute("dir", "auto");
      }
    }

    // Select all <table> elements inside the container that are not already wrapped.
    const tables = container.querySelectorAll("table");
    tables.forEach((table) => {
      // Check if the table is already wrapped to avoid double-wrapping
      if (!table.parentElement.classList.contains("table-container")) {
        const table_wrapper = document.createElement("div");
        table_wrapper.classList.add("table-container");
        table.parentNode.insertBefore(table_wrapper, table);
        table_wrapper.appendChild(table);
      }
    });
  });
}

// Run on DOMContentLoaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", proseCleanupAndTableWrap);
} else {
  proseCleanupAndTableWrap();
}

// Also run on htmx:afterSettle if htmx is present
if (window.htmx) {
  window.htmx.on("htmx:afterSettle", proseCleanupAndTableWrap);
}
