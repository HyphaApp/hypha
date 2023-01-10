(function ($) {

    'use strict';

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

    $(MobileMenu.selector()).each((index, el) => {
        new MobileMenu($(el), $('.js-mobile-menu-close'), $('.header__menus--mobile'), $('.header__search'));
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

    // Setting the CSRF token on AJAX requests.
    var csrftoken = false;
    if (typeof window.Cookies !== 'undefined') {
        csrftoken = window.Cookies.get('csrftoken');
    }
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (csrftoken && !csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
    });

})(jQuery);
