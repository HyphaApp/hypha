// We use htmx.onLoad() so it will initilise file uploads in htmx dialogs.
htmx.onLoad(function () {
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
        const closestFormGroup = input.closest(".form__group");
        if (closestFormGroup) {
          closestFormGroup.style.display = "none";
        }
      });
    }
  }

  // Handle client side validation for required file fields
  let fileInputs = document.querySelectorAll(
    ".dff-uploader input[type='file'][required]"
  );

  fileInputs.forEach((input) => {
    input.addEventListener("invalid", function (event) {
      event.preventDefault(); // Prevent default browser behavior

      // Find the closest dff-uploader wrapper and display an error
      let container = input.closest(".dff-uploader");

      let errorDiv = container.querySelector(".dff-invalid-files");
      if (errorDiv) {
        errorDiv.innerText = "This field is required. Please upload a file."; // Show error message
        errorDiv.style.color = "red";
      }
    });
  });
});
