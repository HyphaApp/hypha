// We use htmx.onLoad() so it will initialise file uploads in htmx dialogs.
// It runs for the body on page load and then for each swapped in element.
htmx.onLoad(function (elt) {
  // Initialize django-file-form for forms that have a `form_id` field
  // added by django-file-form. Include the form the new content was swapped
  // into, it might have been initialised already so it is flagged.
  const forms = new Set(elt.querySelectorAll("form"));
  const parentForm = elt.closest("form");
  if (parentForm) {
    forms.add(parentForm);
  }
  forms.forEach(function (form) {
    if (
      !form.initUploadFieldsDone &&
      form.querySelector("[name=form_id]") &&
      form.querySelector("[data-js-file-upload]")
    ) {
      window.initUploadFields(form);
      form.initUploadFieldsDone = true;
    }
  });

  // Handle client side validation for required file fields.
  const fileSelector = "input[type='file'][required]";
  if (elt.matches(fileSelector)) {
    initValidation(elt);
  }
  elt.querySelectorAll(fileSelector).forEach(initValidation);

  /**
   * Show an error message for a required file field when it is invalid.
   * @param {HTMLInputElement} input The file input.
   */
  function initValidation(input) {
    // The same element can be part of more than one htmx load.
    if (input.fileValidationDone) {
      return;
    }
    input.fileValidationDone = true;

    // The field wrapper, see forms/includes/field.html.
    const container =
      input.closest("[data-js-file-upload]") || input.parentElement;
    const errorId = `${input.id || input.name}-error`;

    // Do not call preventDefault() here, that stops the browser from
    // focusing and scrolling to the field like it does for other fields.
    input.addEventListener("invalid", function () {
      // Reuse the server side error if there is one.
      let errorEl = container.querySelector(".text-error");

      if (!errorEl) {
        errorEl = document.createElement("p");
        errorEl.classList.add("text-error");
        // Place it where server side errors are, right after the widget.
        (input.closest(".dff-uploader") || input).after(errorEl);
      }
      errorEl.id = errorId;
      // Fall back to the browser's localised message for inputs not
      // rendered through forms/includes/field.html.
      errorEl.textContent =
        container.dataset.requiredText || input.validationMessage;

      input.setAttribute("aria-invalid", "true");
      setDescribedBy(input, errorId, true);
    });

    input.addEventListener("change", function () {
      const errorEl = container.querySelector(".text-error");

      // Clear the error only when a file is selected.
      if (
        errorEl &&
        (input.files.length > 0 || container.querySelector(".dff-file"))
      ) {
        errorEl.remove();
        input.removeAttribute("aria-invalid");
        setDescribedBy(input, errorId, false);
      }
    });
  }

  /**
   * Add or remove an id from the aria-describedby attribute of an element.
   * @param {HTMLElement} el The element.
   * @param {string} id The id to add or remove.
   * @param {boolean} add Whether to add or remove the id.
   */
  function setDescribedBy(el, id, add) {
    const ids = (el.getAttribute("aria-describedby") || "")
      .split(" ")
      .filter((value) => value && value !== id);
    if (add) {
      ids.push(id);
    }
    if (ids.length) {
      el.setAttribute("aria-describedby", ids.join(" "));
    } else {
      el.removeAttribute("aria-describedby");
    }
  }
});
