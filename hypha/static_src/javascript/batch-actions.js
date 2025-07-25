/* eslint-disable max-nested-callbacks */
(function ($) {
  const $checkbox = $(".js-batch-select");
  const $allCheckboxInput = $(".js-batch-select-all");
  const $batchButtons = $("[data-js-batch-actions]");
  const $batchTitlesList = $(".js-batch-titles");
  const $batchTitleCount = $(".js-batch-title-count");
  const $hiddenIDlist = $(".js-submissions-id");
  const $hiddenInvoiceIDlist = $(".js-invoices-id");
  const closedClass = "is-closed";

  $(window).on("load", function () {
    updateActionBarVisibility();
    updateCount();
  });

  $allCheckboxInput.change(function () {
    if ($(this).is(":checked")) {
      $checkbox.each(function () {
        this.checked = true;
      });
    } else {
      $checkbox.each(function () {
        this.checked = false;
      });
    }

    updateActionBarVisibility();
    updateCount();
    updateInvoiceProgressButton();
  });

  $checkbox.change(function () {
    // see how many checkboxes are :checked
    updateActionBarVisibility();

    // updates selected checkbox count
    updateCount();

    // reset the check all input
    if (!$(this).is(":checked") && $allCheckboxInput.is(":checked")) {
      resetCheckAllInput();
    }

    updateInvoiceProgressButton();
  });

  // append selected project titles to batch update reviewer modal
  $batchButtons.each(function () {
    $(this).click(function (e) {
      let selectedIDs = [];
      e.preventDefault();
      selectedIDs = prepareBatchListing();

      if (selectedIDs.length > 0) {
        // Get the base URL from the href attribute
        const baseUrl = $(this).attr("href");
        const url = new URL(baseUrl, window.location.origin);
        selectedIDs.forEach((id) => {
          url.searchParams.append("selected_ids", id);
        });
        // Send the request using htmx.ajax
        htmx.ajax("GET", url.toString(), {
          target: "#htmx-modal", // Optional: set the target element
        });
      } else {
        alert("Please select at least one item.");
      }
    });
  });

  /**
   * Prepare the batch listing.
   * @returns {Array} selectedIDs
   */
  function prepareBatchListing() {
    $batchTitlesList.html("");
    $batchTitleCount.html("");
    $batchTitlesList.addClass(closedClass);

    let selectedIDs = [];

    $checkbox.filter(":checked").each(function () {
      selectedIDs.push($(this).parents("tr").data("record-id"));
    });

    $batchTitleCount.append(`${selectedIDs.length} submissions selected`);
    $hiddenIDlist.val(selectedIDs.join(","));
    $hiddenInvoiceIDlist.val(selectedIDs.join(","));
    return selectedIDs;
  }

  /**
   * Update the invoice progress button.
   */
  function updateInvoiceProgressButton() {
    var actions;
    $checkbox.filter(":checked").each(function () {
      let newActions = $(this)
        .parents("tr")
        .find(".js-actions")
        .data("actions");
      // If actions is undefined (i.e., first iteration), initialize it with newActions
      if (!actions) {
        actions = newActions;
      } else {
        // Filter actions to keep only items also present in newActions
        actions = actions.filter((action) => newActions.includes(action));
      }
    });

    const batchInvoiceProgressBtn = document.querySelector(
      "[data-js-batch-actions='invoice-update-status']"
    );

    if (!actions || actions.length === 0) {
      batchInvoiceProgressBtn.setAttribute("disabled", "disabled");
    } else {
      batchInvoiceProgressBtn.removeAttribute("disabled");
    }
  }

  /**
   * Toggle the batch actions.
   */
  function updateActionBarVisibility() {
    const bar = document.querySelector("[data-js-batch-actions-bar]");
    if ($(".js-batch-select:checked").length === 0) {
      bar.classList.add("hidden");
    } else {
      bar.classList.remove("hidden");
    }
  }

  /**
   * Update the count of selected checkboxes.
   */
  function updateCount() {
    const totalSelectionsElement = document.querySelector(
      '[data-js-batch-actions="total-selections"]'
    );
    if (totalSelectionsElement) {
      totalSelectionsElement.innerHTML = document.querySelectorAll(
        ".js-batch-select:checked"
      ).length;
    }
  }

  /**
   * Reset the check all input.
   */
  function resetCheckAllInput() {
    $allCheckboxInput.prop("checked", false);
  }
})(jQuery);
