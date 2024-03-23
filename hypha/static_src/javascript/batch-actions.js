(function ($) {
    "use strict";

    const $body = $("body");
    const $checkbox = $(".js-batch-select");
    const $allCheckboxInput = $(".js-batch-select-all");
    const $batchButtons = $(".js-batch-button");
    const $batchProgress = $(".js-batch-progress");
    const $batchInvoiceProgress = $(".js-batch-invoice-progress");
    const $actionOptions = $("#id_action option");
    const $actionInvoiceOptions = $("#id_invoice_action option");
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
        $(this).click(function () {
            prepareBatchListing();
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
            const link = $(this).parents("tr").find(".js-title").find("a");
            const href = link.attr("href");
            const title = link.data("tippy-content");

            $batchTitlesList.append(`
                <a href="${href}" class="list-reveal__item" target="_blank" rel="noopener noreferrer" title="${title}">
                    ${title}
                    <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="" width="16" height="16" class="inline align-text-bottom w-4 h-4">
                        <path d="M6.22 8.72a.75.75 0 0 0 1.06 1.06l5.22-5.22v1.69a.75.75 0 0 0 1.5 0v-3.5a.75.75 0 0 0-.75-.75h-3.5a.75.75 0 0 0 0 1.5h1.69L6.22 8.72Z"></path>
                        <path d="M3.5 6.75c0-.69.56-1.25 1.25-1.25H7A.75.75 0 0 0 7 4H4.75A2.75 2.75 0 0 0 2 6.75v4.5A2.75 2.75 0 0 0 4.75 14h4.5A2.75 2.75 0 0 0 12 11.25V9a.75.75 0 0 0-1.5 0v2.25c0 .69-.56 1.25-1.25 1.25h-4.5c-.69 0-1.25-.56-1.25-1.25v-4.5Z"></path>
                    </svg>
                </a>
            `);
            selectedIDs.push($(this).parents("tr").data("record-id"));
        });

        $batchTitleCount.append(`${selectedIDs.length} submissions selected`);
        $hiddenIDlist.val(selectedIDs.join(","));
        $hiddenInvoiceIDlist.val(selectedIDs.join(","));
    }

    function updateInvoiceProgressButton() {
        var actions = $actionInvoiceOptions
            .map(function () {
                return this.value;
            })
            .get();
        $checkbox.filter(":checked").each(function () {
            let newActions = $(this)
                .parents("tr")
                .find(".js-actions")
                .data("actions");
            actions = actions.filter((action) => newActions.includes(action));
        });

        $actionInvoiceOptions.each(function () {
            if (!actions.includes(this.value)) {
                $(this).attr("disabled", "disabled");
            } else {
                $(this).removeAttr("disabled");
            }
        });
        $actionInvoiceOptions.filter(":enabled:first").prop("selected", true);
        if (actions.length === 0) {
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
        var actions = $actionOptions
            .map(function () {
                return this.value;
            })
            .get();
        $checkbox.filter(":checked").each(function () {
            let newActions = $(this)
                .parents("tr")
                .find(".js-actions")
                .data("actions");
            actions = actions.filter((action) => newActions.includes(action));
        });
        $actionOptions.each(function () {
            if (!actions.includes(this.value)) {
                $(this).attr("disabled", "disabled");
            } else {
                $(this).removeAttr("disabled");
            }
        });
        $actionOptions.filter(":enabled:first").prop("selected", true);
        if (actions.length === 0) {
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
