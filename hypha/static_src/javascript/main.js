(function ($) {
    "use strict";

    let MobileMenu = class {
        static selector() {
            return ".js-mobile-menu-toggle";
        }

        constructor(node, closeButton, mobileMenu, search) {
            this.node = node;
            this.closeButton = closeButton;
            this.mobileMenu = mobileMenu;

            this.bindEventListeners();
        }

        bindEventListeners() {
            this.node.click(this.toggle.bind(this));
            this.closeButton.click(this.toggle.bind(this));
        }

        toggle() {
            // toggle mobile menu
            this.mobileMenu[0].classList.toggle("is-visible");
        }
    };

    $(MobileMenu.selector()).each((index, el) => {
        new MobileMenu(
            $(el),
            $(".js-mobile-menu-close"),
            $(".header__menus--mobile")
        );
    });

    // reset mobile filters if they're open past the tablet breakpoint
    $(window)
        .resize(function resize() {
            if ($(window).width() > 1024) {
                $(".js-actions-toggle").removeClass("is-active");
                $(".js-actions-sidebar").removeClass("is-visible");
                $(".tr--parent.is-expanded").removeClass("is-expanded");
            }
        })
        .trigger("resize");

    $("form")
        .filter(".form__comments")
        .submit(function (e) {
            var $form = $(this);
            var formValues = $form.serialize();
            var previousValues = $form.attr("data-django-form-submit-last");

            if (previousValues === formValues) {
                // Previously submitted - don't submit again
                e.preventDefault();
            } else {
                $form.attr("data-django-form-submit-last", formValues);
            }
        });

    // Setting the CSRF token on AJAX requests.
    var csrftoken = false;
    if (typeof window.Cookies !== "undefined") {
        csrftoken = window.Cookies.get("csrftoken");
    }
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);
    }
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (
                csrftoken &&
                !csrfSafeMethod(settings.type) &&
                !this.crossDomain
            ) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        },
    });
})(jQuery);
