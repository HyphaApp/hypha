/* eslint-disable no-loop-func */
(function ($) {
    "use strict";

    var i;
    for (i = 2; i < 20; i++) {
        var $field_group = $(".field-group-" + i);
        if ($field_group.length) {
            var classes = "field-group-wrapper field-group-wrapper-" + i;
            $field_group.each(function () {
                if (
                    $(this).data("hidden") &&
                    classes.indexOf("js-hidden") === -1
                ) {
                    classes += " js-hidden";
                }
            });
            $field_group.wrapAll('<div class="' + classes + '" />');
        } else {
            break;
        }
    }

    $('.form-fields-grouper input[type="radio"]').on("change", function () {
        var radio_input_value = $(this).val();
        var fields_grouper_div = this.closest(".form-fields-grouper");
        var fields_grouper_for = $(fields_grouper_div).data("grouper-for");
        var group_toggle_on_value = $(fields_grouper_div).data("toggle-on");
        var group_toggle_off_value = $(fields_grouper_div).data("toggle-off");

        if (radio_input_value === group_toggle_on_value) {
            $(".field-group-wrapper-" + fields_grouper_for)
                .removeClass("js-hidden")
                .addClass("highlighted");
            $(".field-group-" + fields_grouper_for).each(function () {
                if ($(this).data("required") === "True") {
                    $(this)
                        .children(".form__item")
                        .children()
                        .attr("required", true);
                    $(this)
                        .children("label")
                        .append('<span class="form__required">*</span>');
                }
            });
        } else if (radio_input_value === group_toggle_off_value) {
            $(".field-group-wrapper-" + fields_grouper_for)
                .removeClass("highlighted")
                .addClass("js-hidden");
            $(".field-group-" + fields_grouper_for).each(function () {
                $(this)
                    .children(".form__item")
                    .children()
                    .attr("required", false);
                $(this).children("label").children(".form__required").remove();
            });
        }
    });
})(jQuery);
