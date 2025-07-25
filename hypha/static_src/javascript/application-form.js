(function () {
  const form = document.querySelector(".application-form");
  const links = form.querySelectorAll("a");
  const submitButtons = form.querySelectorAll("[type=submit]");
  const required = form.querySelectorAll("input[required]");
  const groups = form.querySelectorAll(".form__group");
  const errors = form.querySelectorAll(".form__error");

  // Make links on application forms open in a new window/tab.
  links.forEach(function (link) {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });

  // Set aria-required attribute true for required fields.
  required.forEach(function (field) {
    field.setAttribute("aria-required", true);
  });

  // Add label_id as aria-describedby to help text.
  groups.forEach(function (group) {
    const label = group.querySelector("label");
    if (label) {
      const label_id = label.getAttribute("for");
      if (group.querySelector(".form__help")) {
        group
          .querySelector(".form__help")
          .setAttribute("aria-describedby", label_id);
      }
    }
  });

  if (errors.length) {
    // Set focus to the first error field.
    const first_error = errors[0].querySelector("input");
    if (first_error) {
      first_error.focus();
    }

    // Set aria-invalid for field with errors.
    errors.forEach(function (error) {
      const input = error.querySelector("input, textarea");
      if (input) {
        input.setAttribute("aria-invalid", true);
      }
    });
  }

  // Block multiple form submits.
  form.addEventListener("submit", function () {
    // Use setTimeout with 0 delay to ensure form submission begins
    // before the buttons are disabled, allowing their values to be included
    setTimeout(function () {
      submitButtons.forEach(function (button) {
        button.setAttribute("disabled", "disabled");
        if (button.textContent) {
          button.dataset.originalText = button.textContent;
          button.textContent = "Submitting...";
        }
      });
    }, 0);
  });

  const unlockApplicationForm = function () {
    form.setAttribute("action", "");
    submitButtons.forEach(function (button) {
      button.removeAttribute("disabled");
    });
  };

  // Unlock form on
  // 1. mouse move
  // 2. touch move
  // 3. tab or enter key pressed
  document.body.addEventListener("mousemove", unlockApplicationForm, {
    once: true,
    passive: true,
  });
  document.body.addEventListener("touchmove", unlockApplicationForm, {
    once: true,
    passive: true,
  });
  document.body.addEventListener(
    "keydown",
    function (e) {
      if (e.key === "Tab" || e.key === "Enter") {
        unlockApplicationForm();
      }
    },
    { once: true, passive: true }
  );
})();
