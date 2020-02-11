(function ($) {

    'use strict';

    $('.wagtail-form, .newsletter-form').each(function () {
        var $protect_form = $(this);
        var $protect_form_button = $protect_form.find('button[type="submit"]');
        var protect_form_action = $protect_form.data('actionpath');

        // Remove the "no javascript" messages
        $('.message-no-js').detach();

        // Wait for a mouse to move, indicating they are human.
        $('body').mousemove(function () {
            // Unlock the form.
            $protect_form.attr('action', protect_form_action);
            $protect_form_button.attr('disabled', false);
        });

        // Wait for a touch move event, indicating that they are human.
        $('body').on('touchmove', function () {
            // Unlock the form.
            $protect_form.attr('action', protect_form_action);
            $protect_form_button.attr('disabled', false);
        });

        // A tab or enter key pressed can also indicate they are human.
        $('body').keydown(function (e) {
            if ((e.keyCode === 9) || (e.keyCode === 13)) {
                // Unlock the form.
                $protect_form.attr('action', protect_form_action);
                $protect_form_button.attr('disabled', false);
            }
        });
    });

})(jQuery);
