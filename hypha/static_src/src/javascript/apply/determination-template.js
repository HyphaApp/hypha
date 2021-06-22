(function ($) {
    'use strict';

    let DeterminationCopy = class {
        constructor(node) {
            this.node = node[0];
            this.bindEventListeners();
        }

        bindEventListeners() {
            this.node.addEventListener('change', (e) => {
                /*
                 * Every time there is a change to the value
                 * in the dropdown, update the message's code
                 * with the template message.
                 */
                const newContent = this.getMatchingCopy(e.target.value);
                this.updateTextArea(newContent);
            }, false);
        }

        getMatchingCopy(value) {
            if (value === '0') {
                return document.querySelector('div[data-type="rejected"]').innerHTML;
            }
            else if (value === '1') {
                return document.querySelector('div[data-type="more_info"]').innerHTML;
            }
            else {
                return document.querySelector('div[data-type="accepted"]').innerHTML;
            }
            return "";
        }

        updateTextArea(text) {
            window.tinyMCE.activeEditor.setContent(text, {format: 'html'});
        }
    };

    /*
     * The template that renders the determination form
     * spits out several hidden inputs that map between
     * a (to us) random field id and a more canonical name.
     * We use that mapping to grab the drop-down box of the
     * required determination field.
     */
    const determination_id = $("#id_determination").val();
    $("#id_" + determination_id).each((index, el) => {
        /*
         * Now that we have hold of that dropdown, we add some
         * event handlers that execute every time its value changes.
         * (see above)
         */
        new DeterminationCopy($(el));
    });

})(jQuery);
