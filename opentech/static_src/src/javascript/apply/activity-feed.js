(function ($) {

    'use strict';

    // Open the activity feed
    $('.js-open-feed').click((e) => {
        e.preventDefault();
        $('body').addClass('no-scroll');
        $('.js-activity-feed').addClass('is-open');
    });

    // Close the activity feed
    $('.js-close-feed').click((e) => {
        e.preventDefault();
        $('body').removeClass('no-scroll');
        $('.js-activity-feed').removeClass('is-open');
    });

    // Show scroll to top of activity feed button on scroll
    $('.js-activity-feed').on('scroll', function () {
        if ($(this).scrollTop() === 0) {
            $('.js-to-top').removeClass('is-visible');
        }
        else {
            $('.js-to-top').addClass('is-visible');
        }
    });

    // Scroll to the top of the activity feed
    $('.js-to-top').click((e) => {
        e.preventDefault();
        $('.js-activity-feed').animate({scrollTop: 0}, 250);
    });

    // Collaps long comments in activity feed.
    $('.feed__item').each(function () {
        var $content = $(this).find('.feed__content');
        var content_height = $content.outerHeight();
        if (content_height > 300) {
            $(this).addClass('feed__item--collaps');
            $(this).append('<p class="feed__show-button"><a class="link link--button link--button--narrow" href="#">Show</a></p>');
        }
    });

    // Allow users to show full comment.
    $('.feed__show-button').find('.link').click(function (e) {
        e.preventDefault();
        $(this).parents('.feed__item').removeClass('feed__item--collaps');
        $(this).parent().detach();
    });

})(jQuery);
