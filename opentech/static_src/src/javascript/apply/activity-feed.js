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
    $('.js-activity-feed').on('scroll', function() {
        $(this).scrollTop() === 0 ? $('.js-to-top').removeClass('is-visible') : $('.js-to-top').addClass('is-visible');
    });

    // Scroll to the top of the activity feed
    $('.js-to-top').click(() => $('.js-activity-feed').animate({ scrollTop: 0 }, 250));

})(jQuery);
