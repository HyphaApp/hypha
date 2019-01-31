(function ($) {

    'use strict';

    const $body = $('body');
    const $checkbox = $('.js-batch-select');
    const $allCheckboxInput = $('.js-batch-select-all');
    const $changeStatusForm = $('.js-batch-update-status');
    const $batchReviewersButton = $('.js-batch-update-reviewers');
    const $batchTitles = $('.js-batch-titles');
    const $hiddenIDlist = $('#id_submission_ids');
    const activeClass = 'batch-actions-enabled';

    $(window).on('load', function () {
        toggleBatchActions();
        updateCount();
    });

    $allCheckboxInput.change(function () {
        if ($(this).is(':checked')) {
            $checkbox.each(function () {
                this.checked = true;
            });
        }
        else {
            $checkbox.each(function () {
                this.checked = false;
            });
        }

        toggleBatchActions();
        updateCount();
    });

    $checkbox.change(function () {
        // see how many checkboxes are :checked
        toggleBatchActions();

        // updates selected checbox count
        updateCount();

        // reset the check all input
        if (!$(this).is(':checked') && $allCheckboxInput.is(':checked')) {
            resetCheckAllInput();
        }
    });

    // append selected project titles to batch update reviewer modal
    $batchReviewersButton.click(function () {
        $batchTitles.html('');
        let selectedIDs = [];

        $checkbox.each(function () {
            if ($(this).is(':checked')) {
                $batchTitles.append(`<p>${$(this).parents('tr').find('.js-title').data('tooltip')}</p>`);
                selectedIDs.push($(this).parents('tr').data('record-id'));
            }
        });
        $hiddenIDlist.val(selectedIDs.join(','));
    });

    function toggleBatchActions() {
        if ($('.js-batch-select:checked').length) {
            $body.addClass(activeClass);
        }
        else {
            $body.removeClass(activeClass);
        }
    }

    function updateCount() {
        $('.js-total-actions').html($('.js-batch-select:checked').length);
    }

    function resetCheckAllInput() {
        $allCheckboxInput.prop('checked', false);
    }

    // change status form handler
    $changeStatusForm.submit(function (e) {
        e.preventDefault();

        $checkbox.each(function () {
            if ($(this).is(':checked')) {
                // console.log($(this).parents('tr').data('record-id')); // tr data-record-id
                // console.log($(this).parents('tr').find('.js-title').data('tooltip')); // project title
            }
        });
    });
})(jQuery);
