(function () {
    "use strict";
    const field_blocks_ids = JSON.parse(
        document.getElementById("block-ids").textContent
    );

    let DeterminationCopy = class {
        static selector() {
            return "#id_" + field_blocks_ids["determination"];
        }

        constructor(node) {
            this.node = node;
            this.bindEventListeners();
        }

        bindEventListeners() {
            this.node.addEventListener(
                "change",
                (e) => {
                    this.getMatchingCopy(e.target.value);
                },
                false
            );
        }

        getMatchingCopy(value) {
            const proposal_form = document.querySelector("#id_proposal_form");
            if (value === "0") {
                this.text = document.querySelector(
                    'div[data-type="rejected"]'
                ).textContent;
                if (proposal_form) {
                    proposal_form.disabled = true;
                    proposal_form.required = false;
                }
            } else if (value === "1") {
                this.text = document.querySelector(
                    'div[data-type="more_info"]'
                ).textContent;
                if (proposal_form) {
                    proposal_form.disabled = true;
                    proposal_form.required = false;
                }
            } else {
                this.text = document.querySelector(
                    'div[data-type="accepted"]'
                ).textContent;
                if (proposal_form) {
                    proposal_form.disabled = false;
                    proposal_form.required = true;
                }
            }
            this.updateTextArea(this.text);
        }

        updateTextArea(text) {
            this.message_box = document.querySelector(
                "#id_" + field_blocks_ids["message"] + "_ifr"
            );
            this.message_box.contentDocument.getElementsByTagName(
                "body"
            )[0].innerHTML = text;
        }
    };

    document.querySelectorAll(DeterminationCopy.selector()).forEach((el) => {
        new DeterminationCopy(el);
    });
    window.addEventListener("load", function (event) {
        const proposal_form_field = document.querySelector("#id_proposal_form");
        if (!proposal_form_field.value) {
            proposal_form_field.disabled = true;
        }
    });
})();
