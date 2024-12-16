/**
 * Adds collapsible functionality with a "Show" button to an element.
 * Triggers on DOM load, checks content height against max height,
 * and adds button if content exceeds max height. Button click reveals full content.
 * @example
 * <div data-js-collapse data-js-collapse-height="320">
 *   <!-- Content goes here -->
 * </div>
 */
(function () {
  document.addEventListener("DOMContentLoaded", function () {
    // Select the element with the data-js-collapse attribute
    const el = document.querySelector("[data-js-collapse]");
    if (!el) {
      return;
    }

    // Get the current full height of the content
    const content_height = el.getBoundingClientRect().height;
    // Read the max height from the data-js-collapse attribute
    // If the attribute is not set, use the default value
    const content_max_height =
      parseInt(el.getAttribute("data-js-collapse-height")) || 320;

    // If the content height is less than or equal to the max height, do nothing
    if (content_height <= content_max_height) {
      return;
    }

    // Create a "Show" button
    const btn_show = document.createElement("button");
    btn_show.classList.add("button", "button--primary", "button--narrow");
    btn_show.textContent = "Show";

    // Create a wrapper for the button with gradient background
    const btn_wrapper = document.createElement("div");
    btn_wrapper.classList.add(
      ..."w-full absolute bottom-0 left-0 text-center pt-8 pb-4 bg-gradient-to-t from-white".split(
        " "
      )
    );
    btn_wrapper.appendChild(btn_show);

    el.append(btn_wrapper);
    el.classList.add("relative", "overflow-hidden");
    el.style.maxHeight = `${content_max_height}px`;

    // Add click event listener to show full content
    btn_show.addEventListener("click", function () {
      el.style.maxHeight = "none";
      btn_wrapper.remove();
    });
  });
})();
