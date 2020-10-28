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
                if (json) {
                    var screeningOptions = $('<p id="screening-options-para">' + json.title + '<a id="screening-options" data-fancybox="" data-src="#screen-application" class="link link--secondary-change" href="#">Screening Options</a></p>');
                    $('.show-screening-options').find('#screening-options-para').remove();
                    $('.show-screening-options').append(screeningOptions);
                    if (yes === true) {
                        $('.icon--dislike').removeClass('icon--dislike-no');
                        $current.find('.icon').addClass('icon--like-yes');
                    }
                    else {
                        $('.icon--like').removeClass('icon--like-yes');
                        $current.find('.icon').addClass('icon--dislike-no');
                    }
                }
            }
        });
    });
})(jQuery);
