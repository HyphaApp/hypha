'use strict';

var MENU = {

  $container: null,
  $nav: null,

  init: function() {
    MENU.$container = $('#stage-nav .main-nav-container');
    MENU.$nav = $('#stage-nav .main-nav');
    MENU.check();
    var timeout = null;
    window.addEventListener('resize', function () {
      clearTimeout(timeout);
      timeout = setTimeout(MENU.check, 250);
    });
  },

  check: function() {
    MENU.$container.removeClass('is-centered');
    if (MENU.$nav.outerHeight() >= MENU.$container.height()) {
      MENU.$container.addClass('is-centered');
    }
  }
};

(function ($) {
  $(document).ready(function () {
    MENU.init();
  });
})(jQuery);
