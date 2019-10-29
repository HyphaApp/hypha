(function ($) {

    'use strict';

    $('.button--flag').on('click', function (e) {
        e.preventDefault();

        var $current = $(this);
        var id = $current.data('id');
        var type = $current.data('type');

        $.ajax({
            url: '/apply/submissions/' + id + '/' + type + '/flag/',
            type: 'POST',
            success: function (json) {
                if (json.result) {
                    $current.addClass('flagged');
                }
                else {
                    $current.removeClass('flagged');
                }
            }
        });

    });

})(jQuery);
