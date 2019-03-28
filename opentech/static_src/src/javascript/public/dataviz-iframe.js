(function ($) {

    'use strict';

    if (window.location.pathname.indexOf('visualizing-otf-application-data') !== -1) {
        var $dataviz_iframe = $('<iframe/>', {
            id: 'dataviz',
            src: 'https://dataviz.opentech.fund/',
            title: 'Visualizing OTF Application Data',
            width: '100%',
            height: '140rem',
            frameborder: 0
        });
        $('.section--share').before($dataviz_iframe);
    }

})(jQuery);
