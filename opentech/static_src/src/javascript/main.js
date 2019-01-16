
(function ($) {

    'use strict';

    let Search = class {
        static selector() {
            return '.js-search-toggle';
        }

        constructor(node, searchForm) {
            this.node = node;
            this.searchForm = searchForm;
            this.bindEventListeners();
        }

        bindEventListeners() {
            this.node.click(this.toggle.bind(this));
        }

        toggle() {
            // show the search
            this.searchForm[0].classList.toggle('is-visible');

            // swap the icons
            this.node[0].querySelector('.header__icon--open-search').classList.toggle('is-hidden');
            this.node[0].querySelector('.header__icon--close-search').classList.toggle('is-unhidden');

            // add modifier to header to be able to change header icon colours
            document.querySelector('.header').classList.toggle('search-open');
        }
    };

    let MobileMenu = class {
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

            // check if search exists
            if (document.body.contains(this.search[0])) {
                // reset the search whenever the mobile menu is toggled
                if (this.search[0].classList.contains('is-visible')) {
                    this.search[0].classList.toggle('is-visible');
                    document.querySelector('.header__inner--menu-open').classList.toggle('header__inner--search-open');
                }
            }

            // reset the search show/hide icons
            if (this.mobileMenu[0].classList.contains('is-visible') && document.body.contains(this.search[0])) {
                document.querySelector('.header__icon--open-search-menu-closed').classList.remove('is-hidden');
                document.querySelector('.header__icon--close-search-menu-closed').classList.remove('is-unhidden');
            }
        }
    };

    let MobileSearch = class {
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
    };

    // Replace no-js with js class if js is enabled.
    document.querySelector('html').classList.replace('no-js', 'js');

    $(MobileMenu.selector()).each((index, el) => {
        new MobileMenu($(el), $('.js-mobile-menu-close'), $('.header__menus--mobile'), $('.header__search'));
    });

    $(Search.selector()).each((index, el) => {
        new Search($(el), $('.header__search'));
    });

    $(MobileSearch.selector()).each((index, el) => {
        new MobileSearch($(el), $('.header__menus--mobile'), $('.header__search'), $('.js-search-toggle'));
    });

    // Close the message
    $('.js-close-message').click((e) => {
        e.preventDefault();
        var message = e.target.closest('.js-message');
        message.classList.add('messages__text--hide');
    });

    // reset mobile filters if they're open past the tablet breakpoint
    $(window).resize(function resize() {
        if ($(window).width() > 1024) {
            $('.js-actions-toggle').removeClass('is-active');
            $('.js-actions-sidebar').removeClass('is-visible');
            $('.tr--parent.is-expanded').removeClass('is-expanded');
        }
    }).trigger('resize');

    $('form').filter('.form__comments').submit(function (e) {
        var $form = $(this);
        var formValues = $form.serialize();
        var previousValues = $form.attr('data-django-form-submit-last');

        if (previousValues === formValues) {
            // Previously submitted - don't submit again
            e.preventDefault();
        }
        else {
            $form.attr('data-django-form-submit-last', formValues);
        }
    });

    // Get the header and admin bar height and set custom prop with value
    $(window).on('load', function () {
        const headerHeight = $('.header').outerHeight();
        const adminbarHeight = $('.admin-bar').outerHeight();
        document.documentElement.style.setProperty('--header-admin-height', headerHeight + adminbarHeight + 'px');
    });
})(jQuery);
