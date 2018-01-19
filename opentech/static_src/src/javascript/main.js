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
});
