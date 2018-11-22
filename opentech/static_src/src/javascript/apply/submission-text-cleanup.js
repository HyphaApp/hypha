(function ($) {

    'use strict';

    $('p').each(function () {
        // Detach (remove) p tag with only whitespace inside.
        if ($.trim($(this).text()) === '') {
            $(this).detach();
        }
    });


})(jQuery);

