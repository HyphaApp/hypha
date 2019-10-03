(function ($) {

    'use strict';

    var word_count_interval;

    const observer_options = {
        childList: true
    };

    const observer = new MutationObserver(function (mutations) {
        mutations.forEach((mutation) => {
            const word_count = mutation.target.innerText.match(/\d+/)[0];
            const word_count_node = document.querySelector('#' + mutation.target.id);
            if (word_count <= 800) {
                word_count_node.classList.remove('word-count-warning');
                word_count_node.classList.remove('word-count-warning-2');
            }
            else if (word_count > 800 && word_count <= 1000) {
                word_count_node.classList.remove('word-count-warning-2');
                word_count_node.classList.add('word-count-warning');
            }
            else if (word_count > 1000) {
                word_count_node.classList.add('word-count-warning-2');
            }
        });
    });

    function word_count_alert() {
        const word_counts = document.querySelectorAll('.mce-wordcount');
        if (word_counts.length > 0) {
            clearInterval(word_count_interval);
        }
        word_counts.forEach((el) => {
            observer.observe(el, observer_options);
        });
    }

    word_count_interval = setInterval(word_count_alert, 300);

})(jQuery);
