jQuery(function ($) {
  // Initialize django-file-form
  $("form")
    .get()
    .forEach(function (form) {
      // Prevent initilising it multiple times and run it for forms
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
    if ($(".form__group--file").length) {
      window.initUploadFields(form);

      // Hide wrapper elements for hidden inputs added by django-file-form
      $("input[type=hidden]").closest(".form__group").hide();
    }
  }
});
