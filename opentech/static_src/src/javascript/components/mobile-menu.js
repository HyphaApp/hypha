class MobileMenu {
    static selector() {
        return '.js-mobile-menu-toggle';
    }

    constructor(node, closeButton, mobileMenu, search) {
        this.node = node;
        this.closeButton = closeButton;
        this.mobileMenu = mobileMenu;
        this.search = search;

        this.bindEventListeners();
    }

    bindEventListeners() {
        this.node.click(this.toggle.bind(this));
        this.closeButton.click(this.toggle.bind(this));
    }

    toggle() {
        // toggle mobile menu
        this.mobileMenu[0].classList.toggle('is-visible');

        // toggle modifier to change position of the search div when the mobile menu is open
        this.search[0].classList.toggle('header__search--mobile-menu-open');

        // reset the search whenever the mobile menu is toggled
        if(this.search[0].classList.contains('is-visible')){
            this.search[0].classList.toggle('is-visible');
            document.querySelector('.header__inner--menu-open').classList.toggle('header__inner--search-open');
        }

        // reset the search show/hide icons
        if(this.mobileMenu[0].classList.contains('is-visible')){
            document.querySelector('.header__icon--open-search-menu-open').classList.remove('is-hidden');
            document.querySelector('.header__icon--close-search-menu-open').classList.remove('is-unhidden');
            document.querySelector('.header__icon--open-search-menu-closed').classList.remove('is-hidden');
            document.querySelector('.header__icon--close-search-menu-closed').classList.remove('is-unhidden');
        }
    }
}

export default MobileMenu;
