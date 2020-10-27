(function ($) {

    'use strict';

    $('.thumb').on('click', function (e) {
        e.preventDefault();

        var $current = $(this);
        var id = $current.data('id');
        var yes = $current.data('yes');

        $.ajax({
            url: '/api/v1/submissions/' + id + '/screening_statuses/default/',
            type: 'POST',
            data: {yes: yes},
            success: function (json) {
                if (json && $('#screening-options').length === 0) {
                    var screeningOptions = $('<p>' + json.title + '<a id="screening-options" data-fancybox="" data-src="#screen-application" class="link link--secondary-change" href="#">Screening Options</a></p>');
                    $('.show-screening-options').append(screeningOptions);
                    if (yes === true) {
                        $current.find('.icon').addClass('icon--like-yes');
                    }
                    else {
                        $current.find('.icon').addClass('icon--dislike-no');
                    }
                }
            }
        });
    });
})(jQuery);
