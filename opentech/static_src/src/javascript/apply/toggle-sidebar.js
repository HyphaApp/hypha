(function ($) {

    'use strict';

    var $sidebar = $('.sidebar');
    $('.tabs__container').append('<a class="tab__item tab__item--right js-sidebar-toggle" href="#">Toggle sidebar</a>');
    $('.js-sidebar-toggle').click(function (e) {
        e.preventDefault();
        $sidebar.toggleClass('hidden');
    });

})(jQuery);

