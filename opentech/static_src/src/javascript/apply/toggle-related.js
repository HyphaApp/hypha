(function ($) {

    'use strict';

    // Collaps long comments in activity feed.
    $('.related-sidebar').each(function () {
        var $content = $(this).find('ul');
        var content_height = $content.outerHeight();
        if (content_height > 300) {
            $(this).addClass('related-sidebar--collaps');
            $(this).append('<p class="related-sidebar__show-button"><a class="link link--button link--button--narrow" href="#">Show</a></p>');
        }
    });

    // Allow users to show full comment.
    $('.related-sidebar__show-button').find('.link').click(function (e) {
        e.preventDefault();
        $(this).parents('.related-sidebar').removeClass('related-sidebar--collaps');
        $(this).parent().detach();
    });

})(jQuery);

