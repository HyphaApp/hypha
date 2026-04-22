(function () {
  "use strict";

  /**
   * Wrap all elements matching a selector into a single wrapper div.
   * Similar to jQuery's wrapAll.
   */
  function wrapAll(elements, wrapperClass) {
    if (!elements.length) return null;
    const wrapper = document.createElement("div");
    wrapper.className = wrapperClass;
    elements[0].parentNode.insertBefore(wrapper, elements[0]);
    elements.forEach(function (el) {
      wrapper.appendChild(el);
    });
    return wrapper;
  }

  /**
   * Add or remove `required` on form inputs within a group element.
   * Uses `data-required="True"` on each fieldset to know which fields
   * should be required when the group is visible.
   */
  function setGroupRequired(wrapper, visible) {
    if (visible) {
      wrapper
        .querySelectorAll("[data-required='True']")
        .forEach(function (fieldset) {
          fieldset
            .querySelectorAll("input:not([type='hidden']), select, textarea")
            .forEach(function (el) {
              el.setAttribute("required", "");
            });
          const labelSpan = fieldset.querySelector(".form__question span");
          if (labelSpan && !labelSpan.querySelector("sup")) {
            const sup = document.createElement("sup");
            sup.textContent = "*";
            labelSpan.appendChild(sup);
          }
        });
    } else {
      wrapper
        .querySelectorAll("input:not([type='hidden']), select, textarea")
        .forEach(function (el) {
          el.removeAttribute("required");
        });
      wrapper
        .querySelectorAll(".form__question span sup")
        .forEach(function (sup) {
          sup.remove();
        });
    }
  }

  // --- Build group wrappers for numeric group_number-based groups ---
  for (var i = 2; i < 20; i++) {
    var groupEls = Array.from(document.querySelectorAll(".field-group-" + i));
    if (!groupEls.length) break;

    var isHidden = groupEls.some(function (el) {
      return el.dataset.hidden === "true";
    });

    var classes = "field-group-wrapper field-group-wrapper-" + i;
    if (isHidden) classes += " js-hidden";

    wrapAll(groupEls, classes);
  }

  // --- Listen for changes on toggle radio buttons ---
  document.querySelectorAll(".form-fields-grouper").forEach(function (grouper) {
    var grouperFor = grouper.dataset.grouperFor;
    var toggleOn = grouper.dataset.toggleOn;
    var toggleOff = grouper.dataset.toggleOff;

    grouper.querySelectorAll('input[type="radio"]').forEach(function (radio) {
      radio.addEventListener("change", function () {
        var wrapper = document.querySelector(
          ".field-group-wrapper-" + grouperFor
        );
        if (!wrapper) return;

        if (this.value === toggleOn) {
          wrapper.classList.remove("js-hidden");
          wrapper.classList.add("highlighted");
          setGroupRequired(wrapper, true);
        } else if (this.value === toggleOff) {
          wrapper.classList.remove("highlighted");
          wrapper.classList.add("js-hidden");
          setGroupRequired(wrapper, false);
        }
      });
    });
  });
})();
