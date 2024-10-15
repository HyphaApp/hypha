(function ($) {
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

    /**
     * Checks that the specified HTTP method doesn't require CSRF protection
     *
     * @param {string} method - HTTP method to check
     * @returns {boolean} true if the method doesn't require CSRF protection, true otherwise.
     */
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
