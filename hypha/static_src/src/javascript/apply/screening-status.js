(function ($) {

    'use strict';

    $('.abcdef').on('click', function (e) {
        e.preventDefault();

        console.log('Coming here');
        var $current = $(this);
        var id = $current.data('id');
        var yes = $current.data('yes');

        $.ajax({
            url: '/api/v1/submissions/' + id + '/screening_statuses/default/',
            type: 'POST',
            data: {yes: yes},
            success: function (json) {
                if (json && $('#screening-options').length === 0) {
                    var screeningOptions = $('<p><a id="screening-options" data-fancybox="" data-src="#screen-application" class="link link--secondary-change" href="#">Screening Options</a></p>');
                    $(screeningOptions).insertAfter($current);
                }
            }
        });
    });

})(jQuery);
