(function ($) {

    'use strict';

    function toggleProposalInfo() {
        $('.js-toggle-propsoal-info').click(function (e) {
            e.preventDefault();
            const activeClass = 'is-open';

            if (this.innerHTML === 'Show more') {
                this.innerHTML = 'Hide';
            }
            else {
                this.innerHTML = 'Show more';
            }

            $(this).toggleClass(activeClass);
            $('.js-grid-hidden').toggleClass(activeClass);
        });
    }

    toggleProposalInfo();

})(jQuery);
