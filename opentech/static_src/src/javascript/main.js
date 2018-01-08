import $ from './globals';
import MobileMenu from './components/mobile-menu';
import DesktopSearch from './components/desktop-search';

// Open the mobile menu callback
function openMobileMenu() {
    document.querySelector('body').classList.add('no-scroll');
    document.querySelector('.header__menus--mobile').classList.add('is-visible');
}

// Close the mobile menu callback.
function closeMobileMenu() {
    document.querySelector('body').classList.remove('no-scroll');
    document.querySelector('.header__menus--mobile').classList.remove('is-visible');
}

$(function () {
    $(MobileMenu.selector()).each((index, el) => {
        new MobileMenu($(el), openMobileMenu, closeMobileMenu);
    });

    $(DesktopSearch.selector()).each((index, el) => {
        new DesktopSearch($(el), $('.header__search--desktop'));
    });

    // Toggle subnav visibility
    $('.js-subnav-back').on('click', function(){
        this.parentNode.classList.remove('is-visible');
    });
});
