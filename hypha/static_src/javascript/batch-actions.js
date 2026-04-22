(function () {
  "use strict";

  const checkboxes = document.querySelectorAll(".js-batch-select");
  const allCheckboxInputs = document.querySelectorAll(".js-batch-select-all");
  const batchButtons = document.querySelectorAll("[data-js-batch-actions]");
  const hiddenIDlists = document.querySelectorAll(".js-submissions-id");

  window.addEventListener("load", function () {
    updateActionBarVisibility();
    updateCount();
  });

  allCheckboxInputs.forEach(function (input) {
    input.addEventListener("change", function () {
      checkboxes.forEach(function (cb) {
        cb.checked = input.checked;
      });
      updateActionBarVisibility();
      updateCount();
      updateInvoiceProgressButton();
    });
  });

  checkboxes.forEach(function (cb) {
    cb.addEventListener("change", function () {
      updateActionBarVisibility();
      updateCount();

      // Reset the check-all input if this one was unchecked
      if (!cb.checked) {
        allCheckboxInputs.forEach(function (all) {
          all.checked = false;
        });
      }

      updateInvoiceProgressButton();
    });
  });

  // Append selected project titles to batch update modal on button click
  batchButtons.forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const selectedIDs = prepareBatchListing();

      if (selectedIDs.length > 0) {
        const baseUrl = btn.getAttribute("href");
        const url = new URL(baseUrl, window.location.origin);
        selectedIDs.forEach(function (id) {
          url.searchParams.append("selected_ids", id);
        });
        htmx.ajax("GET", url.toString(), { target: "#htmx-modal" });
      } else {
        alert("Please select at least one item.");
      }
    });
  });

  /**
   * Build the list of selected IDs and update hidden inputs.
   * @returns {Array} selectedIDs
   */
  function prepareBatchListing() {
    const selectedIDs = Array.from(checkboxes)
      .filter(function (cb) {
        return cb.checked;
      })
      .map(function (cb) {
        return cb.closest("tr").dataset.recordId;
      });

    hiddenIDlists.forEach(function (el) {
      el.value = selectedIDs.join(",");
    });

    return selectedIDs;
  }

  /**
   * Enable/disable the invoice progress button based on common actions
   * across all selected rows.
   */
  function updateInvoiceProgressButton() {
    var actions;
    Array.from(checkboxes)
      .filter(function (cb) {
        return cb.checked;
      })
      .forEach(function (cb) {
        const actionsEl = cb.closest("tr").querySelector(".js-actions");
        if (!actionsEl) return;
        let newActions;
        try {
          newActions = JSON.parse(actionsEl.dataset.actions);
        } catch (e) {
          newActions = [];
        }
        if (!actions) {
          actions = newActions;
        } else {
          actions = actions.filter(function (a) {
            return newActions.includes(a);
          });
        }
      });

    const btn = document.querySelector(
      "[data-js-batch-actions='invoice-update-status']"
    );
    if (!btn) return;

    if (!actions || actions.length === 0) {
      btn.setAttribute("disabled", "disabled");
    } else {
      btn.removeAttribute("disabled");
    }
  }

  /**
   * Show or hide the batch action bar depending on selection state.
   */
  function updateActionBarVisibility() {
    const bar = document.querySelector("[data-js-batch-actions-bar]");
    if (!bar) return;
    const anyChecked = Array.from(checkboxes).some(function (cb) {
      return cb.checked;
    });
    bar.classList.toggle("hidden", !anyChecked);
  }

  /**
   * Update the selected item count display.
   */
  function updateCount() {
    const el = document.querySelector(
      '[data-js-batch-actions="total-selections"]'
    );
    if (el) {
      el.textContent = Array.from(checkboxes).filter(function (cb) {
        return cb.checked;
      }).length;
    }
  }
})();
