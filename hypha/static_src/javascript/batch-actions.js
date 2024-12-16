/* eslint-disable max-nested-callbacks */
(function ($) {
  const $body = $("body");
  const $checkbox = $(".js-batch-select");
  const $allCheckboxInput = $(".js-batch-select-all");
  const $batchButtons = $(".js-batch-button");
  const $batchInvoiceProgress = $(".js-batch-invoice-progress");
  const $batchTitlesList = $(".js-batch-titles");
  const $batchTitleCount = $(".js-batch-title-count");
  const $hiddenIDlist = $(".js-submissions-id");
  const $hiddenInvoiceIDlist = $(".js-invoices-id");
  const $toggleBatchList = $(".js-toggle-batch-list");
  const activeClass = "batch-actions-enabled";
  const closedClass = "is-closed";

  $(window).on("load", function () {
    toggleBatchActions();
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

    toggleBatchActions();
    updateCount();
    updateInvoiceProgressButton();
  });

  $checkbox.change(function () {
    // see how many checkboxes are :checked
    toggleBatchActions();

    // updates selected checbox count
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

  $batchInvoiceProgress.click(function () {
    updateInvoiceProgressButton();
  });

  // show/hide the list of actions
  $toggleBatchList.click((e) => {
    e.preventDefault();

    if ($(".js-batch-titles").hasClass(closedClass)) {
      $toggleBatchList.html("Hide");
    } else {
      $toggleBatchList.html("Show");
    }

    $batchTitlesList.toggleClass(closedClass);
  });

  /**
   * Prepare the batch listing.
   * @returns {Array} selectedIDs
   */
  function prepareBatchListing() {
    $batchTitlesList.html("");
    $batchTitleCount.html("");
    $batchTitlesList.addClass(closedClass);
    $toggleBatchList.html("Show");

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

    if (!actions || actions.length === 0) {
      $batchInvoiceProgress.attr("disabled", "disabled");
      $batchInvoiceProgress.attr(
        "data-tooltip",
        "Status changes can't be applied to Invoices with this combination of statuses"
      );
    } else {
      $batchInvoiceProgress.removeAttr("disabled");
      $batchInvoiceProgress.removeAttr("data-tooltip");
    }
  }

  /**
   * Toggle the batch actions.
   */
  function toggleBatchActions() {
    if ($(".js-batch-select:checked").length) {
      $body.addClass(activeClass);
    } else {
      $body.removeClass(activeClass);
    }
  }

  /**
   * Update the count of selected checkboxes.
   */
  function updateCount() {
    $(".js-total-actions").html($(".js-batch-select:checked").length);
  }

  /**
   * Reset the check all input.
   */
  function resetCheckAllInput() {
    $allCheckboxInput.prop("checked", false);
  }
})(jQuery);
