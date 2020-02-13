'use strict';

/**
 * Capture and emit the window scroll event
 * Bind to the event using: `$(document).bind('on-scroll', fn);
 * Custom event is throttled by time and distance scrolled
 */

var SCROLL = {

  throttleDuration: 250,
  lastScrollPosition: window.scrollY,
  ticking: false,
  debounceTimeout: null,

  init: function() {
    window.addEventListener('scroll', SCROLL.onSroll);
  },

  onSroll: function() {
    if (!SCROLL.ticking) {
      SCROLL.ticking = true;
      window.requestIdleCallback(function() {
        SCROLL.debounce();
        SCROLL.ticking = false;
      });
    }
  },

  distanceCheck: function() {
    const scrollY = window.scrollY;
    if (scrollY > SCROLL.lastScrollPosition + 2 || scrollY < SCROLL.lastScrollPosition - 2) {
      SCROLL.lastScrollPosition = scrollY;
      return true;
    }
    return false;
  },

  debounce: function() {
    clearTimeout(SCROLL.debounceTimeout);
    SCROLL.debounceTimeout = setTimeout(function() {
      $(document).trigger('on-scroll');
    }, SCROLL.debounceDuration);
  },

};

(function($) {
  $(document).ready(function() {
    SCROLL.init();
  });
})(jQuery);
