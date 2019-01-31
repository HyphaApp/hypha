(function ($) {

    'use strict';

    const $body = $('body');
    const $checkbox = $('.js-batch-select');
    const $allCheckboxInput = $('.js-batch-select-all');
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
        $batchTitlesList.removeClass(closedClass);
        $toggleBatchList.html('Hide');

        let selectedIDs = [];

        $checkbox.each(function () {
            if ($(this).is(':checked')) {
                const href = $(this).parents('tr').find('.js-title').find('a').attr('href');
                const title = $(this).parents('tr').find('.js-title').data('tooltip');

                $batchTitlesList.append(`
                    <a href="${href}" class="modal__list-item" target="_blank" rel="noopener noreferrer" title="${title}">
                        ${title}
                        <svg class="modal__open-link-icon"><use xlink:href="#open-in-new-tab"></use></svg>
                    </a>
                `);
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
})(jQuery);
