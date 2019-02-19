(function ($) {

    'use strict';

    const $body = $('body');
    const $checkbox = $('.js-batch-select');
    const $allCheckboxInput = $('.js-batch-select-all');
    const $batchButtons = $('.js-batch-button');
    const $batchProgress = $('.js-batch-progress');
    const $actionOptions = $('#id_action option');
    const $batchTitlesList = $('.js-batch-titles');
    const $batchTitleCount = $('.js-batch-title-count');
    const $hiddenIDlist = $('.js-submissions-id');
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
        updateProgressButton();
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

        updateProgressButton();
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

    function prepareBatchListing() {
        $batchTitlesList.html('');
        $batchTitleCount.html('');
        $batchTitlesList.addClass(closedClass);
        $toggleBatchList.html('Show');

        let selectedIDs = [];

        $checkbox.filter(':checked').each(function () {
            const href = $(this).parents('tr').find('.js-title').find('a').attr('href');
            const title = $(this).parents('tr').find('.js-title').data('tooltip');

            $batchTitlesList.append(`
                <a href="${href}" class="modal__list-item" target="_blank" rel="noopener noreferrer" title="${title}">
                    ${title}
                    <svg class="modal__open-link-icon"><use xlink:href="#open-in-new-tab"></use></svg>
                </a>
            `);
            selectedIDs.push($(this).parents('tr').data('record-id'));
        });

        $batchTitleCount.append(`${selectedIDs.length} submissions selected`);
        $hiddenIDlist.val(selectedIDs.join(','));
    }

    function updateProgressButton() {
        var actions = $actionOptions.map(function () { return this.value; }).get();
        $checkbox.filter(':checked').each(function () {
            let newActions = $(this).parents('tr').find('.js-actions').data('actions');
            actions = actions.filter(action => newActions.includes(action));
        });
        $actionOptions.each(function () {
            if (!actions.includes(this.value)) {
                $(this).attr('disabled', 'disabled');
            }
            else {
                $(this).removeAttr('disabled');
            }
        });
        $actionOptions.filter(':enabled:first').prop('selected', true);
        if (actions.length === 0) {
            $batchProgress.attr('disabled', 'disabled');
        }
        else {
            $batchProgress.removeAttr('disabled');
        }
    }


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
