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
            const firstErrorField = $error_fields[0];
            const firstInputEl =
                firstErrorField.querySelector("input, textarea");
            if (firstInputEl) {
                firstInputEl.focus();
            }

            $error_fields.each(function (index, error_field) {
                const inputEl = error_field.querySelector("input, textarea");
                if (inputEl) {
                    inputEl.setAttribute("aria-invalid", true);
                }
            });
        }

        // Remove the "no javascript" messages
        $(".message-no-js").detach();

        // Wait for a mouse to move, indicating they are human.
        $("body").mousemove(function () {
            // Unlock the form.
            $application_form.attr("action", "");
            $application_form_button.attr("disabled", false);
        });

        // Wait for a touch move event, indicating that they are human.
        $("body").on("touchmove", function () {
            // Unlock the form.
            $application_form.attr("action", "");
            $application_form_button.attr("disabled", false);
        });

        // A tab or enter key pressed can also indicate they are human.
        $("body").keydown(function (e) {
            if (e.keyCode === 9 || e.keyCode === 13) {
                // Unlock the form.
                $application_form.attr("action", "");
                $application_form_button.attr("disabled", false);
            }
        });
    });
})(jQuery);
