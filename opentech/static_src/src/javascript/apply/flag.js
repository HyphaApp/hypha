(function ($) {

    'use strict';

    $('.flagged-table').find('.all-submissions-table__parent').each(function () {
        var $flagged_item = $(this);
        var submission_id = $flagged_item.data('record-id');
        var flag_type = $flagged_item.data('flag-type');
        var $button = '<span class="button--float"><button class="button button--flag button--unflag flagged" data-id="' + submission_id + '" data-type="' + flag_type + '">Flag</button></span>';
        $flagged_item.find('td.comments').css('position', 'relative').append($button);
    });

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
