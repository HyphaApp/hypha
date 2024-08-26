(function () {
    "use strict";

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
        calculate_score();

        filtered_selectors.forEach((selector) => {
            selector.addEventListener("change", calculate_score);
        });
    }

    function calculate_score() {
        let score = 0;
        filtered_selectors.forEach((selector) => {
            const value = parseInt(selector.value);

            if (!isNaN(value) && value !== 99) {
                score += value;
            }
        });

        // Update the text in .form--score-box with the current score
        document.querySelector(".form--score-box").textContent =
            "Score: " + score;
    }
})();
