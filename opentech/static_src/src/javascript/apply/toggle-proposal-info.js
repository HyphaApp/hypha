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
            $('.js-rich-text-hidden').toggleClass(activeClass);
        });
    }

    toggleProposalInfo();

})(jQuery);
