(function ($) {

    'use strict';

    // Make external links on application forms open in a new window/tab.
    $('.application-form').find("a[href^='http']").attr('target', '_blank');

})(jQuery);
