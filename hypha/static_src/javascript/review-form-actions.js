(function () {
  /**
   * Show dialog if user have changed the form and not saved.
   * @param {object} f - form element
   * @returns {object} - form contents
   */
  function formContents(f) {
    // Thanks to https://stackoverflow.com/a/44033425
    return Array.from(new FormData(f), function (e) {
      return e.map(encodeURIComponent).join("=");
    }).join("&");
  }

  // Show dialog if user have changed the form and not saved.
  document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("#review-form-edit");
    const original = formContents(form);

    window.onbeforeunload = function () {
      const formNow = formContents(form);
      if (formNow !== original) {
        return false;
      }
    };

    form.addEventListener("submit", function () {
      window.onbeforeunload = null;
    });
  });
})();
