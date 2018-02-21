import jQuery from './globals';
import MobileMenu from './components/mobile-menu';
import Search from './components/search';
import MobileSearch from './components/mobile-search';

(function ($) {
    // remove no-js class if js is enabled
    document.querySelector('html').classList.remove('no-js');

    $(MobileMenu.selector()).each((index, el) => {
        new MobileMenu($(el), $('.js-mobile-menu-close'), $('.header__menus--mobile'), $('.header__search'));
    });

    $(Search.selector()).each((index, el) => {
        new Search($(el), $('.header__search'));
    });

    $(MobileSearch.selector()).each((index, el) => {
        new MobileSearch($(el), $('.header__menus--mobile'), $('.header__search'), $('.js-search-toggle'));
    });

    // Show list of selected files for upload on input[type=file]
    $('input[type=file]').change(function() {
        for (let i = 0; i < $(this)[0].files.length; ++i) {
            $(this).parents('.form__item').prepend(`
                <p>${$(this)[0].files[i].name}</p>
            `);
        }
    });

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
    $('.js-open-filters').on('click', (e) => {
        e.target.nextElementSibling.classList.add('is-open');
        $('.js-filter-list').addClass('form__filters--mobile');
    });

    // close mobile filters
    $('.js-close-filters').on('click', (e) => {
        e.target.parentElement.parentElement.classList.remove('is-open');
        $('.js-filter-list').removeClass('form__filters--mobile');
    });

    // clear all filters
    $('.js-clear-filters').on('click', () =>{
        const dropdowns = document.querySelectorAll('.form__filters--mobile select');
        dropdowns.forEach(dropdown => {
            $(dropdown).val(null).trigger('change');
            $('.select2-selection.is-active').removeClass('is-active');
            mobileFilterPadding(dropdown);
        });
    });

    function mobileFilterPadding (element) {
        const dropdown = $(element).closest('.select2');
        const openDropdown = $('.select2 .expanded');
        let dropdownMargin = 0;
        if(openDropdown.length > 0 && !openDropdown.hasClass('select2-container--open')){
            openDropdown.removeClass('expanded');
            if (dropdown.position().top > openDropdown.position().top ){
                dropdownMargin = parseInt(openDropdown.css('marginBottom'));
            }
            openDropdown.css('margin-bottom', '0px');
        }
        if(dropdown.hasClass('select2-container--open')){
            dropdown.addClass('expanded');
            const id = $(element).closest('.select2-selection').attr('aria-owns');
            const match = $(`ul#${id}`);
            const positionalMatch = match.closest('.select2-container');
            const margin = match.outerHeight(true);
            dropdown.css('margin-bottom', `${margin}px`);
            positionalMatch.css('top', positionalMatch.position().top - dropdownMargin);
        }

    }

    // reset mobile filters if they're open past the tablet breakpoint
    $(window).resize(function resize(){
        if ($(window).width() < 768) {
            $('.select2').on('click', (e) => {
                mobileFilterPadding(e.target);
            });
        }
    }).trigger('resize');
})(jQuery);

// wait for DOM content to load before checking for select2
document.addEventListener('DOMContentLoaded', () => {
    // Add active class to select2 checkboxes after page has been filtered
    const clearButtons = document.querySelectorAll('.select2-selection__clear');
    clearButtons.forEach(clearButton => {
        clearButton.parentElement.parentElement.classList.add('is-active');
    });
});
