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

    if (window.location.pathname.indexOf('impacts-and-outcomes') !== -1) {
        var $dataviz_iframe2 = $('<iframe/>', {
            id: 'dataviz',
            src: 'https://dataviz.opentech.fund/impacts/',
            title: 'Impacts and Outcomes',
            width: '100%',
            height: '550rem',
            frameborder: 0
        });
        $('.rich-text').before($dataviz_iframe2);
    }

})(jQuery);
