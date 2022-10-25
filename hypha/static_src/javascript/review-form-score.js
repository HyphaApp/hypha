(function ($) {
    "use strict";

    // grab all the selectors
    const selectors = Array.prototype.slice.call(
        document.querySelectorAll("select")
    );

    if (selectors.length > 1) {
        // remove recommendation select box from array
        selectors.shift();
        selectors.forEach(function (selector) {
            selector.onchange = calculate_score;
        });
    }

    function calculate_score() {
        let score = 0;
        selectors.forEach(function (selector) {
            score += parseInt(selector.value);
        });
        $(".form--score-box").text("Score: " + score);
    }
})(jQuery);
