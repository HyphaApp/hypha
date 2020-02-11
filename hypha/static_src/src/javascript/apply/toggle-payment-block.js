(function ($) {

    'use strict';

    function togglePaymentBlock() {
        $('.js-payment-block-rejected-link').click(function (e) {
            e.preventDefault();

            this.innerHTML = (this.innerHTML === 'Show rejected') ? 'Hide rejected' : 'Show rejected';

            $('.js-payment-block-rejected-table').toggleClass('is-hidden');
        });
    }

    togglePaymentBlock();

})(jQuery);
