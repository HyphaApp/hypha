(function ($) {
    "use strict";

    $(".application-form").each(function () {
        var $application_form = $(this);
        var $application_form_button = $application_form.find(
            'button[type="submit"]'
        );

        // set aria-required attribute true for required fields
        $application_form
            .find("input[required]")
            .each(function (index, input_field) {
                input_field.setAttribute("aria-required", true);
            });

        // add label_id as aria-describedby to help texts
        $application_form
            .find(".form__group")
            .each(function (index, form_group) {
                var label = form_group.querySelector("label");
                if (label) {
                    var label_id = label.getAttribute("for");
                    if (form_group.querySelector(".form__help")) {
                        form_group
                            .querySelector(".form__help")
                            .setAttribute("aria-describedby", label_id);
                    }
                }
            });

        // set aria-invalid for field with errors
        var $error_fields = $application_form.find(".form__error");
        if ($error_fields.length) {
            // set focus to the first error field
            $error_fields[0].querySelector("input").focus();

            $error_fields.each(function (index, error_field) {
                const inputEl = error_field.querySelector("input, textarea");
                if (inputEl) {
                    inputEl.setAttribute("aria-invalid", true);
                }
            });
        }

        // Remove the "no javascript" messages
        $(".message-no-js").detach();

        const unlockApplicationForm = function () {
            $application_form.attr("action", "");
            $application_form_button.attr("disabled", false);
        };

        // Unlock form on
        // 1. mouse move
        // 2. touch move
        // 3. tab or enter key pressed
        document.body.addEventListener("mousemove", unlockApplicationForm, {
            once: true,
        });
        document.body.addEventListener("touchmove", unlockApplicationForm, {
            once: true,
        });
        document.body.addEventListener(
            "keydown",
            function (e) {
                if (e.key === "Tab" || e.key === "Enter") {
                    unlockApplicationForm();
                }
            },
            { once: true }
        );
    });
})(jQuery);
