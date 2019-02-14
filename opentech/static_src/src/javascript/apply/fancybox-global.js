(function ($) {

    'use strict';

    $('[data-fancybox]').fancybox({
        animationDuration: 350,
        animationEffect: 'fade',
        afterClose: function () {
            $('.django-select2-checkboxes').select2('close');
        }
    });

    // Close any open select2 dropdowns when inside a modal
    $('.modal').click((e) => {
        if (e.target.classList.contains('select2-selection__rendered')) {
            return;
        }
        $('.django-select2-checkboxes').select2('close');
    });

    $(document).ready(
        $('.modal').each((idx, element) => {
            var modal = $(element);
            var error = modal.has('.errorlist');
            if (error.length) {
                const modalID = modal.attr('id');
                const buttonTrigger = $(`[data-src="#${modalID}"]`);
                buttonTrigger[0].click();
            }
        })
    );

})(jQuery);
