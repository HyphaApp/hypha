(function ($) {
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
