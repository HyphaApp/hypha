(function ($) {

    'use strict';

    function toggleActionsPanel(){
        $('.js-actions-toggle').click(function(e) {
            e.preventDefault();
            this.classList.toggle('is-active');
            this.nextElementSibling.classList.toggle('is-visible');
        });
    }

    // Show actions sidebar on mobile
    toggleActionsPanel();

})(jQuery);
