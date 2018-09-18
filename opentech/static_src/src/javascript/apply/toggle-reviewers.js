(function ($) {

    'use strict';

    // get all the reviewers that are missing
    const reviewers = Array.prototype.slice.call($('.js-reviews-sidebar').find('tr.hidden.no-response'));

    $('.js-toggle-reviewers').click(function(e) {
        e.preventDefault();

        // toggle class and update text
        $(this).toggleClass('is-open');
        $(this).hasClass('is-open') ? $(this).html('Hide All Assigned Advisors') : $(this).html('All Assigned Advisors');

        // toggle the reviewers
        toggleReviewers(reviewers);
    });

    // show/hide the reviewers
    function toggleReviewers(reviewers) {
        reviewers.forEach(((reviewer) => {
            $(reviewer).toggleClass('hidden');
        }));
    }

})(jQuery);
