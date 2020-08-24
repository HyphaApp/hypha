(function ($) {

    'use strict';

    // Make links on application forms open in a new window/tab.
  $('.application-form').find('a').not('h2 > a').not('h3 > a').not('h4 > a').attr({
        target: '_blank',
        rel: 'noopener noreferrer'
    });

})(jQuery);
