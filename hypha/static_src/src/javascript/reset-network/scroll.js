/* eslint-env jquery */

(function () {

    'use strict';

    var SCROLL = {

        isTouch: false,

        init: function () {

            // Is touch?
            if ('ontouchstart' in document.documentElement) {
                document.documentElement.classList.add('is-touch');
                SCROLL.isTouch = true;
            }
            else {
                document.documentElement.classList.add('is-not-touch');
            }

            SCROLL.EVENT.init();
        },

        // *********************************************************************
        // ****************************** EVENT ********************************
        // *********************************************************************

        /**
         * Capture and emit the window scroll event
         * Bind to the event using: `$(document).bind('on-scroll', fn);
         * Throttled by time and distance scrolled
         */
        EVENT: {

            throttleDuration: 250,
            lastScrollPosition: window.scrollY,
            ticking: false,
            debounceTimeout: null,

            init: function () {
                window.addEventListener('scroll', SCROLL.EVENT.onSroll);
            },

            onSroll: function () {
                if (!SCROLL.EVENT.ticking) {
                    SCROLL.EVENT.ticking = true;
                    if (window.requestIdleCallback) {
                        window.requestIdleCallback(function () {
                            SCROLL.EVENT.debounce();
                            SCROLL.EVENT.ticking = false;
                        });
                    }
                    else {
                        SCROLL.EVENT.debounce();
                        SCROLL.EVENT.ticking = false;
                    }
                }
            },

            distanceCheck: function () {
                const scrollY = window.scrollY;
                if (scrollY > SCROLL.EVENT.lastScrollPosition + 2 || scrollY < SCROLL.EVENT.lastScrollPosition - 2) {
                    SCROLL.EVENT.lastScrollPosition = scrollY;
                    return true;
                }
                return false;
            },

            debounce: function () {
                clearTimeout(SCROLL.EVENT.debounceTimeout);
                SCROLL.EVENT.debounceTimeout = setTimeout(function () {
                    $(document).trigger('on-scroll');
                }, SCROLL.EVENT.debounceDuration);
            }
        }

    };

    (function ($) {
        $(document).ready(function () {
            SCROLL.init();
        });
    })(jQuery);

})();
