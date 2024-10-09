(function () {
    "use strict";

    let use_average = false;

    // grab all the selectors
    const selectors = Array.prototype.slice.call(
        document.querySelectorAll("select")
    );

    if (selectors.length > 1) {
        document.querySelector(".form--score-box").style.display = "block";
        calculate_score();
        selectors.forEach((selector) => {
            selector.addEventListener("change", calculate_score);
        });
        // Look also for the avg/total button
        const toggleAverageButton = document.querySelector(
            ".form--score-box button"
        );
        toggleAverageButton.addEventListener("click", toggle_use_average);
    }

    function calculate_score() {
        const formatter = new Intl.NumberFormat({
            maximumSignificantDigits: 4,
        });
        let total = 0;
        let count = 0;
        selectors.forEach((selector) => {
            const value = parseInt(selector.value);

            if (!isNaN(value) && value !== 99) {
                count += 1;
                total += value;
            }
        });
        let score = total;

        if (use_average) {
            score = total / count;
        }

        // Update the text in .form--score-box with the current score
        document.querySelector(".form--score-box .score-number").textContent =
            formatter.format(score);
    }

    function toggle_use_average() {
        use_average = !use_average;
        calculate_score();
    }
})();
