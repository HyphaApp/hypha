(function ($) {

    'use strict';

    $('.form-fields-grouper input[type="radio"]').change(function () {
        var radio_input_value = $(this).val();
        var fields_grouper_div = this.closest('.form-fields-grouper ');
        var fields_grouper_for = $(fields_grouper_div).attr('data-grouper-for');
        var group_toggle_on_value = $(fields_grouper_div).attr('data-toggle-on');
        var group_toggle_off_value = $(fields_grouper_div).attr('data-toggle-off');

        if (radio_input_value === group_toggle_on_value) {
            $('.field-group-' + fields_grouper_for).show();
        }
        else if (radio_input_value === group_toggle_off_value) {
            $('.field-group-' + fields_grouper_for).hide();
        }
    });

})(jQuery);
