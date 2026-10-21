// We use htmx.onLoad() so it will initialise file uploads in htmx dialogs.
htmx.onLoad(function () {
  // Extract DOM element references
  const forms = document.querySelectorAll("form");
  const fileGroups = document.querySelectorAll("[data-js-file-upload]");
  const hiddenInputs = document.querySelectorAll("input[type=hidden]");
  const fileInputs = document.querySelectorAll("input[type='file'][required]");

  // Initialize django-file-form
  forms.forEach(function (form) {
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
    if (fileGroups.length) {
      window.initUploadFields(form);

      // Hide wrapper elements for hidden inputs added by django-file-form
      hiddenInputs.forEach(function (input) {
        const closestFormGroup = input.closest(".form__group");
        if (closestFormGroup) {
          closestFormGroup.style.display = "none";
        }
      });
    }
  }

  // Handle client side validation for required file fields
  fileInputs.forEach((input) => {
    // The field wrapper, see forms/includes/field.html.
    const container =
      input.closest("[data-js-file-upload]") || input.parentElement;

    // Do not call preventDefault() here, that stops the browser from
    // focusing and scrolling to the field like it does for other fields.
    input.addEventListener("invalid", function () {
      const errorMessage =
        container.dataset.requiredText || "This field is required.";

      let errorEl = container.querySelector(".text-error");

      if (!errorEl) {
        errorEl = document.createElement("p");
        errorEl.classList.add("text-error");
        container.appendChild(errorEl);
      }
      errorEl.innerText = errorMessage; // Show error message
    });

    input.addEventListener("change", function () {
      const errorEl = container.querySelector(".text-error");

      // Clear the error only when a file is selected
      if (
        errorEl &&
        (input.files.length > 0 || container.querySelector(".dff-file"))
      ) {
        errorEl.remove();
      }
    });
  });
});
