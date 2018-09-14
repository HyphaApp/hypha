(function ($) {

    'use strict';

    let DeterminationCopy = class {
        static selector(){
            return '#id_outcome';
        }

        constructor(node) {
            this.node = node[0];
            this.bindEventListeners();
        }

        bindEventListeners(){
            this.node.addEventListener('change', (e) => {
                this.getMatchingCopy(e.target.value);
            }, false);
        }

        getMatchingCopy(value) {
            if (value === '0'){
                this.text = document.querySelector('div[data-type="rejected"]').textContent;
            } else if (value === '1') {
                this.text = document.querySelector('div[data-type="more_info"]').textContent;
            } else {
                this.text = document.querySelector('div[data-type="accepted"]').textContent;
            }
            this.updateTextArea(this.text);
        }

        updateTextArea(text) {
            window.tinyMCE.get('id_message').setContent(text);
        }
    };

    $(DeterminationCopy.selector()).each((index, el) => {
        new DeterminationCopy($(el));
    });

})(jQuery);
