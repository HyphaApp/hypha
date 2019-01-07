(function ($) {

    'use strict';

    const $body = $('body');
    const $toggleButton = $('.js-toggle-filters');
    const $closeButton = $('.js-close-filters');
    const $clearButton = $('.js-clear-filters');
    const filterOpenClass = 'filters-open';
    const submissionsUrl = '/apply/submissions/';
    const filterActiveClass = 'is-active';

    // check if the page has a query string and keep filters open if so on desktop
    if (window.location.href.indexOf('?') > -1 && $(window).width() > 1024) {
        $body.addClass(filterOpenClass);
        updateButtonText();
    }

    // Add active class to filters - dropdowns are dynamically appended to the dom,
    // so we have to listen for the event higher up
    $body.on('click', '.select2-dropdown', (e) => {
        // get the id of the dropdown
        let selectId = e.target.parentElement.parentElement.id;

        // find the matching dropdown
        let match = $(`.select2-selection[aria-owns="${selectId}"]`);

        // if the dropdown contains a clear class, the filters are active
        if ($(match[0]).find('span.select2-selection__clear').length !== 0) {
            match[0].classList.add(filterActiveClass);
        }
        else {
            match[0].classList.remove(filterActiveClass);
        }
    });

    // remove active class on clearing select2
    $('.select2').on('select2:unselecting', (e) => {
        const dropdown = e.target.nextElementSibling.firstChild.firstChild;
        if (dropdown.classList.contains(filterActiveClass)) {
            dropdown.classList.remove(filterActiveClass);
        }
    });

    // toggle filters
    $toggleButton.on('click', () => {
        if ($body.hasClass(filterOpenClass)) {
            handleClearFilters();
        }

        $body.toggleClass(filterOpenClass);
        updateButtonText();
    });

    // close filters on mobile
    $closeButton.on('click', (e) => {
        $body.removeClass(filterOpenClass);
        updateButtonText();
    });

    // redirect to submissions home to clear filters
    function handleClearFilters() {
        window.location.href = submissionsUrl;
    }

    // toggle filters button wording
    function updateButtonText() {
        if ($body.hasClass(filterOpenClass)) {
            $toggleButton.text('Clear filters');
        }
        else {
            $toggleButton.text('Filters');
        }
    }

    // clear all filters
    $clearButton.on('click', () => {
        const dropdowns = document.querySelectorAll('.form__filters select');
        dropdowns.forEach(dropdown => {
            $(dropdown).val(null).trigger('change');
            $('.select2-selection.is-active').removeClass(filterActiveClass);
            mobileFilterPadding(dropdown); // eslint-disable-line no-undef
        });
    });

    $(function () {
        // Add active class to select2 checkboxes after page has been filtered
        const clearButtons = document.querySelectorAll('.select2-selection__clear');
        clearButtons.forEach(clearButton => {
            clearButton.parentElement.parentElement.classList.add(filterActiveClass);
        });
    });

})(jQuery);

