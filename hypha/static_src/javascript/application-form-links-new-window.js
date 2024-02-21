(function ($) {
    "use strict";

    // Make links on application forms open in a new window/tab.
    $(".application-form").find("a").not(".section-head a").attr({
        target: "_blank",
        rel: "noopener noreferrer",
    });
})(jQuery);
