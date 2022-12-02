(function ($) {
    "use strict";
    $(document).ready(function () {
        var form = $("form");
        var original = form.serialize();

        window.onbeforeunload = function () {
            if (form.serialize() !== original) {
                return "Are you sure you want to leave?";
            }
        };

        form.submit(function () {
            window.onbeforeunload = null;
        });

        // grab all the selectors
        let filtered_selectors;
        const selectors = Array.prototype.slice.call(
            document.querySelectorAll("select")
        );
        if (selectors.length > 1) {
            document.querySelector(".form--score-box").style.display = "block";
            // remove recommendation select box from array
            filtered_selectors = selectors.filter(
                (selector) => selector[0].text !== "Need More Info"
            );
            filtered_selectors.forEach(function (selector) {
                selector.onchange = calculate_score;
            });
            calculate_score();
        }
        function calculate_score() {
            let score = 0;
            filtered_selectors.forEach(function (selector) {
                const value = parseInt(selector.value);
                if (!isNaN(value) && value !== 99) {
                    score += value;
                }
            });
            $(".form--score-box").text("Score: " + score);
        }
    });
})(jQuery);
