import $ from './globals';
import MobileMenu from './components/mobile-menu';
import Search from './components/search';
import MobileSearch from './components/mobile-search';

$(function () {
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
});
