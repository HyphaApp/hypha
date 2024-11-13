(function ($) {
    const $body = $("body");
    const $checkbox = $(".js-batch-select");
    const $allCheckboxInput = $(".js-batch-select-all");
    const $batchButtons = $(".js-batch-button");
    const $batchProgress = $(".js-batch-progress");
    const $batchInvoiceProgress = $(".js-batch-invoice-progress");
    const $batchTitlesList = $(".js-batch-titles");
    const $batchTitleCount = $(".js-batch-title-count");
    const $hiddenIDlist = $(".js-submissions-id");
    const $hiddenInvoiceIDlist = $(".js-invoices-id");
    const $batchDetermineSend = $(".js-batch-determine-send");
    const $batchDetermineConfirm = $(".js-batch-determine-confirm");
    const $batchDetermineForm = $batchDetermineSend.parent("form");
    const $toggleBatchList = $(".js-toggle-batch-list");
    const activeClass = "batch-actions-enabled";
    const closedClass = "is-closed";

    $batchDetermineSend.click(function (e) {
        if (!$batchDetermineForm[0].checkValidity()) {
            $batchDetermineForm.submit();
            e.preventDefault();
        }
    });

    $batchDetermineConfirm.click(function (e) {
        $batchDetermineForm.find(":submit").click();
        e.preventDefault();
    });

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
        updateProgressButton();
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

        updateProgressButton();
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
                selectedIDs.forEach(id => {
                    url.searchParams.append("selected_ids", id);
                });
                // Send the request using htmx.ajax
                htmx.ajax('GET', url.toString(), {
                    target: '#htmx-modal' // Optional: set the target element
                });
            } else {
                alert("Please select at least one item.");
            }
        });
    });

    $batchProgress.click(function () {
        updateProgressButton();
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

    function updateProgressButton() {
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
            $batchProgress.attr("disabled", "disabled");
            $batchProgress.attr(
                "data-tooltip",
                "Status changes can't be applied to submissions with this combination of statuses"
            );
        } else {
            $batchProgress.removeAttr("disabled");
            $batchProgress.removeAttr("data-tooltip");
        }
    }

    function toggleBatchActions() {
        if ($(".js-batch-select:checked").length) {
            $body.addClass(activeClass);
        } else {
            $body.removeClass(activeClass);
        }
    }

    function updateCount() {
        $(".js-total-actions").html($(".js-batch-select:checked").length);
    }

    function resetCheckAllInput() {
        $allCheckboxInput.prop("checked", false);
    }
})(jQuery);
