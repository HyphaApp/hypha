(function ($) {

    'use strict';

    $('.application-form').each(function () {
        var $application_form = $(this);
        var $application_form_button = $application_form.find('button[type="submit"]');

        // Remove the "no javascript" messages
        $('.message-no-js').detach();

        // Wait for a mouse to move, indicating they are human.
        $('body').mousemove(function () {
            // Unlock the form.
            $application_form.attr('action', '');
            $application_form_button.attr('disabled', false);
        });

        // Wait for a touch move event, indicating that they are human.
        $('body').on('touchmove', function () {
            // Unlock the form.
            $application_form.attr('action', '');
            $application_form_button.attr('disabled', false);
        });

        // A tab or enter key pressed can also indicate they are human.
        $('body').keydown(function (e) {
            if ((e.keyCode === 9) || (e.keyCode === 13)) {
                // Unlock the form.
                $application_form.attr('action', '');
                $application_form_button.attr('disabled', false);
            }
        });
    });

})(jQuery);
