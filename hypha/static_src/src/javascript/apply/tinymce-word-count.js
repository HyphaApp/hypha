(function ($) {
    "use strict";

    var word_count_interval;

    const observer_options = {
        childList: true,
    };

    function word_count(el) {
        let word_count;
        try {
            word_count = parseInt(el.innerText.match(/\d+/)[0], 10);
        } catch (e) {
            word_count = 0;
        }
        const word_limit = parseInt(
            $(el).parents().eq(4).attr("data-word-limit"),
            10
        );
        const percent_to_get = 20;
        const word_limit_to_show_warning =
            word_limit - (percent_to_get / 100) * word_limit;

        if (word_count <= word_limit_to_show_warning) {
            el.setAttribute("data-after-word-count", " out of " + word_limit);
            el.classList.remove("word-count-warning");
            el.classList.remove("word-count-warning-2");
        } else if (
            word_count > word_limit_to_show_warning &&
            word_count <= word_limit
        ) {
            el.setAttribute(
                "data-after-word-count",
                " out of " + word_limit + " (Close to the limit)"
            );
            el.classList.remove("word-count-warning-2");
            el.classList.add("word-count-warning");
        } else if (word_count > word_limit) {
            el.setAttribute(
                "data-after-word-count",
                " out of " + word_limit + " (Over the limit)"
            );
            el.classList.add("word-count-warning-2");
        }
    }

    const observer = new MutationObserver(function (mutations) {
        mutations.forEach((mutation) => {
            word_count(mutation.target);
        });
    });

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
})(jQuery);
