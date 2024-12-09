(function () {
    var word_count_interval;

    const observer_options = {
        childList: true,
    };

    /**
     * Count the words in the element and set the warning classes.
     * @param {object} el - The element to count the words in.
     */
    function word_count(el) {
        let word_count;
        try {
            word_count = parseInt(el.innerText.match(/\d+/)[0], 10);
        } catch {
            word_count = 0;
        }
        const word_limit = parseInt(
            el.closest("div[data-word-limit]").dataset.wordLimit,
            10
        );
        const percent_to_get = 20;
        const word_limit_to_show_warning =
            word_limit - (percent_to_get / 100) * word_limit;

        if (el.textContent.includes("characters")) {
            delete el.dataset.afterWordCount;
            el.classList.remove("word-count-warning");
            el.classList.remove("word-count-warning-2");
        } else if (word_count <= word_limit_to_show_warning) {
            el.dataset.afterWordCount = " out of " + word_limit;
            el.classList.remove("word-count-warning");
            el.classList.remove("word-count-warning-2");
        } else if (
            word_count > word_limit_to_show_warning &&
            word_count <= word_limit
        ) {
            el.dataset.afterWordCount = " out of " + word_limit + " (Close to the limit)";
            el.classList.remove("word-count-warning-2");
            el.classList.add("word-count-warning");
        } else if (word_count > word_limit) {
            el.dataset.afterWordCount = " out of " + word_limit + " (Over the limit)";
            el.classList.add("word-count-warning-2");
        }
    }

    const observer = new MutationObserver(function (mutations) {
        mutations.forEach((mutation) => {
            word_count(mutation.target);
        });
    });

    /**
     * Set the word count on the element and observe for changes.
     */
    function word_count_alert() {
        const word_counts = document.querySelectorAll(
            ".tox-statusbar__wordcount"
        );
        if (word_counts.length > 0) {
            clearInterval(word_count_interval);
        }
        word_counts.forEach((el) => {
            // Run first to set all word count values on initial form.
            word_count(el);
            // Then observe for changes.
            observer.observe(el, observer_options);
        });
    }

    word_count_interval = setInterval(word_count_alert, 300);
})();
