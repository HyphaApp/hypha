import $ from './../globals';
import mobileFilterPadding from './mobile-filter-padding';

export default () => {
    const $openButton = $('.js-open-filters');
    const $closeButton = $('.js-close-filters');
    const $clearButton = $('.js-clear-filters');
    const $filterList = $('.js-filter-list');
    const $filterWrapper = $('.js-filter-wrapper');

    // Add active class to filters - dropdowns are dynamically appended to the dom,
    // so we have to listen for the event higher up
    $('body').on('click', '.select2-dropdown', (e) => {
        // get the id of the dropdown
        let selectId = e.target.parentElement.parentElement.id;

        // find the matching dropdown
        let match = $(`.select2-selection[aria-owns="${selectId}"]`);

        // if the dropdown contains a clear class, the filters are active
        if($(match[0]).find('span.select2-selection__clear').length !== 0) {
            match[0].classList.add('is-active');
        } else {
            match[0].classList.remove('is-active');
        }
    });

    // remove active class on clearing select2
    $('.select2').on('select2:unselecting', (e) => {
        const dropdown = e.target.nextElementSibling.firstChild.firstChild;
        (dropdown.classList.contains('is-active')) ? dropdown.classList.remove('is-active') : null;
    });

    // open mobile filters
    $openButton.on('click', (e) => {
        $('body').addClass('no-scroll');
        $(e.target).next($filterWrapper).addClass('is-open');
        $filterList.addClass('form__filters--mobile');
    });

    // close mobile filters
    $closeButton.on('click', (e) => {
        $('body').removeClass('no-scroll');
        $(e.target).closest($filterWrapper).removeClass('is-open');
        $filterList.removeClass('form__filters--mobile');
    });

    // clear all filters
    $clearButton.on('click', () => {
        const dropdowns = document.querySelectorAll('.form__filters--mobile select');
        dropdowns.forEach(dropdown => {
            $(dropdown).val(null).trigger('change');
            $('.select2-selection.is-active').removeClass('is-active');
            mobileFilterPadding(dropdown);
        });
    });

    // wait for DOM content to load before checking for select2
    document.addEventListener('DOMContentLoaded', () => {
        // Add active class to select2 checkboxes after page has been filtered
        const clearButtons = document.querySelectorAll('.select2-selection__clear');
        clearButtons.forEach(clearButton => {
            clearButton.parentElement.parentElement.classList.add('is-active');
        });
    });
};
