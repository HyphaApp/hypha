document.addEventListener("DOMContentLoaded", function () {
  // Initialize django-file-form
  document.querySelectorAll("form").forEach(function (form) {
    // Prevent initializing it multiple times and run it for forms
    // that have a `form_id` field added by django-file-form.
    if (!form.initUploadFieldsDone && form.querySelector("[name=form_id]")) {
      init(form);
      form.initUploadFieldsDone = true;
    }
  });

  /**
   * Initialize django-file-form for a form.
   * @param {object} form The form to initialize.
   */
  function init(form) {
    if (document.querySelectorAll(".form__group--file").length) {
      window.initUploadFields(form);

      // Hide wrapper elements for hidden inputs added by django-file-form
      document.querySelectorAll("input[type=hidden]").forEach(function (input) {
        var closestFormGroup = input.closest(".form__group");
        if (closestFormGroup) {
          closestFormGroup.hidden = true;
        }
      });
    }
  }
});
