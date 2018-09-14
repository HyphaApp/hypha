(function ($) {

    'use strict';

    // Close the message
    $('.js-close-message').click((e) => {
        e.preventDefault();
        var message = e.target.closest('.js-message');
        message.classList.add('messages__text--hide');
    });

})(jQuery);
