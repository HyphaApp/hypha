(function ($) {
    "use strict";

    function generateTooltips() {
        // get the investments titles
        const titles = Array.prototype.slice.call(
            document.querySelectorAll(".js-title")
        );

        // if the tile has been truncated...
        titles.forEach(function (title) {
            if (title.textContent.indexOf("...") >= 0) {
                addToolTip(title);
            }
        });

        // ...add a tooltip class
        function addToolTip(title) {
            title.classList.add("has-tooltip");
        }
    }

    // Add tooltips to truncated titles on investments overview table
    generateTooltips();
})(jQuery);
