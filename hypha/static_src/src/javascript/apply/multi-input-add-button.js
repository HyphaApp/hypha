(function ($) {

    'use strict';

    $('.multi-input-add-btn').click(function () {
        var allElements = document.getElementsByClassName('multi-input-field-hidden');
        if (allElements.hasOwnProperty(0)) {
            allElements[0].className = 'multi-input-field-show';
        }
    });
})(jQuery);
