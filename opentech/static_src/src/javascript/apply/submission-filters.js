(function ($) {

    'use strict';

    // Variables
    const $toggleButton = $('.js-toggle-filters');
    const $closeButton = $('.js-close-filters');
    const $clearButton = $('.js-clear-filters');
    const filterOpenClass = 'filters-open';
    const filterActiveClass = 'is-active';

    const urlParams = new URLSearchParams(window.location.search);

    const persistedParams = ['sort', 'query', 'submission'];

    // check if the page has a query string and keep filters open if so on desktop
    const minimumNumberParams = persistedParams.reduce(
        (count, param) => count + urlParams.has(param) ? 1 : 0,
        0
    );

    if ([...urlParams].length > minimumNumberParams && $(window).width() > 1024) {
        $('.filters').addClass(filterOpenClass);
        $('.js-toggle-filters').text('Clear filters');
    }

    // Add active class to filters - dropdowns are dynamically appended to the dom,
    // so we have to listen for the event higher up
    $('body').on('click', '.select2-dropdown', (e) => {
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
    $toggleButton.on('click', (e) => {
        // find the nearest filters
        const filters = e.target.closest('.js-table-actions').nextElementSibling;

        if (filters.classList.contains(filterOpenClass)) {
            handleClearFilters();
        }
        else {
            filters.classList.add(filterOpenClass);
            // only update button text on desktop
            if (window.innerWidth >= 1024) {
                updateButtonText(e.target, filters);
            }
        }
    });

    // close filters on mobile
    $closeButton.on('click', (e) => {
        e.target.closest('.filters').classList.remove(filterOpenClass);
    });

    // redirect to submissions home to clear filters
    function handleClearFilters() {
        const query = persistedParams.reduce(
            (query, param) => query + (urlParams.get(param) ? `&${param}=${urlParams.get(param)}` : ''), '?');
        window.location.href = window.location.href.split('?')[0] + query;
    }

    // toggle filters button wording
    function updateButtonText(button, filters) {
        if (filters.classList.contains(filterOpenClass)) {
            button.textContent = 'Clear filters';
        }
        else {
            button.textContent = 'Filters';
        }
    }

    // corrects spacing of dropdowns when toggled on mobile
    function mobileFilterPadding(element) {
        const expanded = 'expanded-filter-element';
        const dropdown = $(element).closest('.select2');
        const openDropdown = $('.select2 .' + expanded);
        let dropdownMargin = 0;

        if (openDropdown.length > 0 && !openDropdown.hasClass('select2-container--open')) {
            // reset the margin of the select we previously worked
            openDropdown.removeClass(expanded);
            // store the offset to adjust the new select box (elements above the old dropdown unaffected)
            if (dropdown.position().top > openDropdown.position().top) {
                dropdownMargin = parseInt(openDropdown.css('marginBottom'));
            }
            openDropdown.css('margin-bottom', '0px');
        }

        if (dropdown.hasClass('select2-container--open')) {
            dropdown.addClass(expanded);
            const dropdownID = $(element).closest('.select2-selection').attr('aria-owns');
            // Element which has the height of the select dropdown
            const match = $(`ul#${dropdownID}`);
            const dropdownHeight = match.outerHeight(true);

            // Element which has the position of the dropdown
            const positionalMatch = match.closest('.select2-container');

            // Pad the bottom of the select box
            dropdown.css('margin-bottom', `${dropdownHeight}px`);

            // bump up the dropdown options by height of closed elements
            positionalMatch.css('top', positionalMatch.position().top - dropdownMargin);
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

    // reset mobile filters if they're open past the tablet breakpoint
    $(window).resize(function resize() {
        if ($(window).width() < 1024) {
            // close the filters if open when reducing the window size
            $('body').removeClass('filters-open');

            // update filter button text
            $('.js-toggle-filters').text('Filters');

            // Correct spacing of dropdowns when toggled
            $('.select2').on('click', (e) => {
                mobileFilterPadding(e.target);
            });
        }
    }).trigger('resize');

})(jQuery);
