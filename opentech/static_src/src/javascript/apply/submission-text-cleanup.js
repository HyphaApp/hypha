(function ($) {

    'use strict';

    $('.rich-text--answers').find('p').each(function () {
        // Detach (remove) p tag with only whitespace inside.
        if ($.trim($(this).text()) === '') {
            $(this).detach();
        }
    });

    // Wrap all tables in a div so overflow auto works.
    $('.rich-text--answers').find('table').wrap('<div class="rich-text__table"></div>');

})(jQuery);
