(function ($) {

    'use strict';
    const field_blocks_ids = JSON.parse(document.getElementById('block-ids').textContent);

    let DeterminationCopy = class {
        static selector() {
            return ('#id_' + field_blocks_ids['determination']);
        }

        constructor(node) {
            this.node = node[0];
            this.bindEventListeners();
        }

        bindEventListeners() {
            this.node.addEventListener('change', (e) => {
                this.getMatchingCopy(e.target.value);
            }, false);
        }

        getMatchingCopy(value) {
            if (value === '0') {
                this.text = document.querySelector('div[data-type="rejected"]').textContent;
            }
            else if (value === '1') {
                this.text = document.querySelector('div[data-type="more_info"]').textContent;
            }
            else {
                this.text = document.querySelector('div[data-type="accepted"]').textContent;
            }
            this.updateTextArea(this.text);
        }

        updateTextArea(text) {
            this.message_box = document.querySelector('#id_' + field_blocks_ids['message'] + '_ifr');
            this.message_box.contentDocument.getElementsByTagName('body')[0].innerHTML = text;
        }
    };

    $(DeterminationCopy.selector()).each((index, el) => {
        new DeterminationCopy($(el));
    });

})(jQuery);
