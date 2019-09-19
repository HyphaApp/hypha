(function ($) {

    'use strict';

    const observer_options = {
        childList: true
    };

    const observer = new MutationObserver(function (mutations) {
        mutations.forEach((mutation) => {
            const word_count = mutation.target.innerText.match(/\d+/)[0];
            const word_count_node = document.querySelector('#' + mutation.target.id);
            if (word_count <= 170) {
                word_count_node.classList.remove('word-count-warning');
                word_count_node.classList.remove('word-count-warning-2');
            }
            else if (word_count > 170 && word_count <= 200) {
                word_count_node.classList.remove('word-count-warning-2');
                word_count_node.classList.add('word-count-warning');
            }
            else if (word_count > 200) {
                word_count_node.classList.add('word-count-warning-2');
            }
        });
    });

    function word_count_alert() {
        const word_counts = document.querySelectorAll('.mce-wordcount');
        word_counts.forEach((el) => {
            observer.observe(el, observer_options);
        });
    }

    window.setTimeout(word_count_alert, 5000);

})(jQuery);



