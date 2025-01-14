(function ($) {
  // Variables
  const $toggleButton = $(".js-toggle-filters");
  const $closeButton = $(".js-close-filters");
  const $clearButton = $(".js-clear-filters");
  const filterOpenClass = "filters-open";
  const filterActiveClass = "is-active";

  const urlParams = new URLSearchParams(window.location.search);

  const persistedParams = ["sort", "query", "submission"];

  // check if the page has a query string and keep filters open if so on desktop
  const minimumNumberParams = persistedParams.reduce(
    (count, param) => (count + urlParams.has(param) ? 1 : 0),
    0
  );

  if ([...urlParams].length > minimumNumberParams && $(window).width() > 1024) {
    $(".filters").addClass(filterOpenClass);
    $(".js-toggle-filters").text("Clear filters");
  }

  // toggle filters
  $toggleButton.on("click", (e) => {
    // find the nearest filters
    const filters = e.target.closest(".js-table-actions").nextElementSibling;

    if (filters.classList.contains(filterOpenClass)) {
      handleClearFilters();
    } else {
      filters.classList.add(filterOpenClass);
      // only update button text on desktop
      if (window.innerWidth >= 1024) {
        updateButtonText(e.target, filters);
      }
    }
  });

  // close filters on mobile
  $closeButton.on("click", (e) => {
    e.target.closest(".filters").classList.remove(filterOpenClass);
  });

  /**
   * Redirect to submissions home to clear filters.
   */
  function handleClearFilters() {
    const query = persistedParams.reduce(
      (query, param) =>
        query +
        (urlParams.get(param) ? `&${param}=${urlParams.get(param)}` : ""),
      "?"
    );
    window.location.href = window.location.href.split("?")[0] + query;
  }

  /**
   * Toggle filters button wording.
   * @param {object} button - button element
   * @param {string} filters - filters element
   */
  function updateButtonText(button, filters) {
    if (filters.classList.contains(filterOpenClass)) {
      button.textContent = "Clear filters";
    } else {
      button.textContent = "Filters";
    }
  }

  // clear all filters
  $clearButton.on("click", () => {
    const dropdowns = document.querySelectorAll(".form__filters select");
    dropdowns.forEach((dropdown) => {
      $(dropdown).val(null).trigger("change");
    });
  });

  // reset mobile filters if they're open past the tablet breakpoint
  $(window)
    .resize(function resize() {
      if ($(window).width() < 1024) {
        // close the filters if open when reducing the window size
        $(".filters").removeClass("filters-open");

        // update filter button text
        $(".js-toggle-filters").text("Filters");
      } else {
        $(".filters").addClass("filters-open");
      }
    })
    .trigger("resize");

  $("#show-filters-button").on("click", () => {
    $(".filters").addClass("filters-open");
  });
})(jQuery);
