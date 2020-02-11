(function ($) {

    'use strict';

    function pastReportsPagination() {
        $('.js-data-block-pagination').click((e) => {
            e.preventDefault();
            showNextTen();
        });
    }

    function showNextTen() {
        const [...nextTen] = $('.js-past-reports-table tr.is-hidden').slice(0, 10);
        nextTen.forEach(item => item.classList.remove('is-hidden'));
        checkRemaining();
    }

    function checkRemaining() {
        const [...remaining] = $('.js-past-reports-table tr.is-hidden');
        if (remaining.length === 0) {
            $('.js-data-block-pagination').addClass('is-hidden');
        }
    }

    pastReportsPagination();

})(jQuery);
