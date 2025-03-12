(function ($) {
  /**
   * This script is used to paginate the past reports table.
   */
  function pastReportsPagination() {
    $(".js-data-block-pagination").click((e) => {
      e.preventDefault();
      showNextTen();
    });
  }

  /**
   * Show next ten.
   */
  function showNextTen() {
    const [...nextTen] = $(".js-past-reports-table tr.hidden").slice(0, 10);
    nextTen.forEach((item) => item.classList.remove("hidden"));
    checkRemaining();
  }

  /**
   * Check remaining.
   */
  function checkRemaining() {
    const [...remaining] = $(".js-past-reports-table tr.hidden");
    if (remaining.length === 0) {
      $(".js-data-block-pagination").addClass("hidden");
    }
  }

  pastReportsPagination();
})(jQuery);
