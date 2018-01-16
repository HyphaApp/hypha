class MobileSearch {
    static selector() {
        return '.js-mobile-search-toggle';
    }

    constructor(node, mobileMenu, searchForm, searchToggleButton) {
        this.node = node;
        this.mobileMenu = mobileMenu[0];
        this.searchForm = searchForm[0];
        this.searchToggleButton = searchToggleButton[0];
        this.bindEventListeners();
    }

    bindEventListeners() {
        this.node.click(this.toggle.bind(this));
    }

    toggle() {
        // hide the mobile menu
        this.mobileMenu.classList.remove('is-visible');

        // wait for the mobile menu to close
        setTimeout(() => {
            // open the search
            this.searchForm.classList.add('is-visible');

            // swap the icons
            this.searchToggleButton.querySelector('.header__icon--open-search').classList.add('is-hidden');
            this.searchToggleButton.querySelector('.header__icon--close-search').classList.add('is-unhidden');
        }, 250);
    }
}

export default MobileSearch;
