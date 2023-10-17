(function ($) {
    "use strict";

    // add the toggle arrow before the investments titles
    $(".all-investments-table__parent td.title").prepend(
        '<span class="all-investments-table__toggle js-toggle-investment"><span class="arrow"></span></span>'
    );

    // grab all the toggles
    const children = Array.prototype.slice.call(
        document.querySelectorAll(".js-toggle-investment")
    );

    // show/hide the investment child rows
    children.forEach(function (child) {
        child.addEventListener("click", (e) => {
            $(e.target)
                .closest(".all-investments-table__parent")
                .toggleClass("is-expanded");
        });
    });
})(jQuery);
