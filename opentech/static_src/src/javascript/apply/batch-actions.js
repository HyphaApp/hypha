(function ($) {

    'use strict';

    const $body = $('body');
    const $checkbox = $('.js-batch-select');
    const $allCheckboxInput = $('.js-batch-select-all');
    const $changeStatusForm = $('.js-batch-update-status');
    const $batchReviewersButton = $('.js-batch-update-reviewers');
    const $batchTitlesList = $('.js-batch-titles');
    const $batchTitleCount = $('.js-batch-title-count');
    const $hiddenIDlist = $('#id_submission_ids');
    const $toggleBatchList = $('.js-toggle-batch-list');
    const activeClass = 'batch-actions-enabled';
    const closedClass = 'is-closed';

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
        $batchTitlesList.html('');
        $batchTitleCount.html('');
        let selectedIDs = [];

        $checkbox.each(function () {
            if ($(this).is(':checked')) {
                $batchTitlesList.append(`<p class="modal__list-item">${$(this).parents('tr').find('.js-title').data('tooltip')}</p>`);
                selectedIDs.push($(this).parents('tr').data('record-id'));
            }
        });

        $batchTitleCount.append(`${selectedIDs.length} submissions selected`);
        $hiddenIDlist.val(selectedIDs.join(','));
    });

    // show/hide the list of actions
    $toggleBatchList.click(e => {
        e.preventDefault();

        if ($('.js-batch-titles').hasClass(closedClass)) {
            $toggleBatchList.html('Hide');
        }
        else {
            $toggleBatchList.html('Show');
        }

        $batchTitlesList.toggleClass(closedClass);
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
