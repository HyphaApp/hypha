(function ($) {

    'use strict';

    $('.form__wagtail-form').each(function () {
        var $wagtail_form = $(this);
        var $wagtail_form_button = $wagtail_form.find('button[type="submit"]');
        var wagtail_form_action = $wagtail_form.data('pageurl');

        // Remove the "no javascript" messages
        $('.message-no-js').detach();

        // Wait for a mouse to move, indicating they are human.
        $('body').mousemove(function () {
            // Unlock the form.
            $wagtail_form.attr('action', wagtail_form_action);
            $wagtail_form_button.attr('disabled', false);
        });

        // Wait for a touch move event, indicating that they are human.
        $('body').on('touchmove', function () {
            // Unlock the form.
            $wagtail_form.attr('action', wagtail_form_action);
            $wagtail_form_button.attr('disabled', false);
        });

        // A tab or enter key pressed can also indicate they are human.
        $('body').keydown(function (e) {
            if ((e.keyCode === 9) || (e.keyCode === 13)) {
                // Unlock the form.
                $wagtail_form.attr('action', wagtail_form_action);
                $wagtail_form_button.attr('disabled', false);
            }
        });
    });

})(jQuery);
