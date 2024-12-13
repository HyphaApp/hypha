/* eslint-disable max-nested-callbacks */
(function () {
    for (let i = 2; i < 20; i++) {
        const field_group = document.querySelectorAll(".field-group-" + i);
        if (field_group.length) {
            let classes = "field-group-wrapper field-group-wrapper-" + i;
            field_group.forEach(function (el) {
                if (el.dataset.hidden && classes.indexOf("js-hidden") === -1) {
                    classes += " js-hidden";
                }
            });
            var wrapper = document.createElement("div");
            wrapper.className = classes;
            field_group[0].parentNode.insertBefore(wrapper, field_group[0]);
            wrapper.appendChild(field_group[0]);
        } else {
            break;
        }
    }

    document
        .querySelectorAll('.form-fields-grouper input[type="radio"]')
        .forEach(function (radio) {
            radio.addEventListener("change", function () {
                const radio_input_value = this.value;
                const fields_grouper_div = this.closest(".form-fields-grouper");
                const fields_grouper_for =
                    fields_grouper_div.dataset.grouperFor;
                const group_toggle_on_value =
                    fields_grouper_div.dataset.toggleOn;
                const group_toggle_off_value =
                    fields_grouper_div.dataset.toggleOff;

                if (radio_input_value === group_toggle_on_value) {
                    var wrapper_on = document.querySelector(
                        ".field-group-wrapper-" + fields_grouper_for
                    );
                    wrapper_on.classList.remove("js-hidden");
                    wrapper_on.classList.add("highlighted");
                    document
                        .querySelectorAll(".field-group-" + fields_grouper_for)
                        .forEach(function (el) {
                            if (el.dataset.required === "True") {
                                el.querySelectorAll(".form__item > *").forEach(
                                    function (child) {
                                        child.required = true;
                                    }
                                );
                                const label = el.querySelector("label");
                                if (label) {
                                    const span = document.createElement("span");
                                    span.classList.add("form__required");
                                    span.textContent = "*";
                                    label.appendChild(span);
                                }
                            }
                        });
                } else if (radio_input_value === group_toggle_off_value) {
                    const wrapper_off = document.querySelector(
                        ".field-group-wrapper-" + fields_grouper_for
                    );
                    wrapper_off.classList.remove("highlighted");
                    wrapper_off.classList.add("js-hidden");
                    document
                        .querySelectorAll(".field-group-" + fields_grouper_for)
                        .forEach(function (el) {
                            el.querySelectorAll(".form__item > *").forEach(
                                function (child) {
                                    delete child.required;
                                }
                            );
                            const span = el.querySelector(
                                "label .form__required"
                            );
                            if (span) {
                                span.remove();
                            }
                        });
                }
            });
        });
})();
