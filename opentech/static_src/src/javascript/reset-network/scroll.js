/* eslint-env jquery */

(function () {

    'use strict';

    var SCROLL = {

        init: function () {

            // Is touch?
            if ('ontouchstart' in document.documentElement) {
                document.documentElement.classList.add('is-touch');
            }
            else {
                document.documentElement.classList.add('is-not-touch');
            }

            SCROLL.EVENT.init();
            SCROLL.LOCK.init();
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
        },

        // *********************************************************************
        // ************************** SCROLL LOCK ******************************
        // *********************************************************************

        LOCK: {

            scrollSpeed: 350,
            themes: [],
            timeout: null,
            $scroll: null,
            scrolling: false,

            init: function () {
                var $doc = $(document);
                SCROLL.LOCK.$scroll = $('html, body');

                // on scroll
                // what section are you over (is clipped by page top)
                // if scrolled 50% or less snap back to start BUT if scrolled an amount that's great than half the height then don't (allow user to
                // continue reading the section
                // if scrolled more than 50% then move onto the end of the section (unless some of the section is below the fold)

                $doc.bind('on-scroll', SCROLL.LOCK.onScroll);
                $doc.bind('section-themes', function (e, data) {
                    SCROLL.LOCK.themes = data;
                });

            },

            onScroll: function () {
                if (!SCROLL.LOCK.themes.length) {
                    return;
                }

                var scrollTop = window.scrollY;

                for (var i = 0; i < SCROLL.LOCK.themes.length; i++) {
                    var section = SCROLL.LOCK.themes[i];
                    var $section = $(section.$section);
                    var sectionScrollTop = section.scrollY;
                    var sectionScrollBottom = $section.outerHeight() + sectionScrollTop;

                    // Find the section currently clipped by the top of the viewport
                    if (scrollTop >= sectionScrollTop && scrollTop < sectionScrollBottom) {
                        SCROLL.LOCK.lockScroll($section, scrollTop, sectionScrollTop, sectionScrollBottom);
                        break;
                    }
                }
            },

            lockScroll: function ($section, scrollTop, sectionScrollTop, sectionScrollBottom) {
                clearTimeout(SCROLL.LOCK.timeout);

                // Prevent disruption to a current scroll to animation
                if (SCROLL.LOCK.scrolling) {
                    return;
                }

                // Only scroll lock on the homepage
                if (!$('#hero-carousel').length) {
                    return;
                }

                // Don't scroll lock if user is near the bottom
                if (window.scrollY + window.innerHeight > $(document).height() - 100) {
                    return;
                }

                SCROLL.LOCK.$scroll.stop();
                SCROLL.LOCK.timeout = setTimeout(function () {
                    var clippedPortionTop = scrollTop - sectionScrollTop;
                    var clippedPortionBottom = sectionScrollBottom - (scrollTop + window.innerHeight);
                    clippedPortionBottom = clippedPortionBottom < 0 ? 0 : clippedPortionBottom;
                    var sectionHeight = sectionScrollBottom - sectionScrollTop;
                    var clippedPercent = (clippedPortionTop / sectionHeight) * 100;
                    var scrollTo = null;

                    // console.log('clippedPortionTop', clippedPortionTop);
                    // console.log('clippedPortionBottom', clippedPortionBottom);
                    // console.log('sectionHeight', sectionHeight);
                    // console.log('clippedPercent', clippedPercent);

                    // Less than half of the section has been scrolled
                    if (clippedPercent <= 50) {

                        // Quanitity of the section scrolled is considerable (is the amount scrolled over half the viewport height)?
                        if (clippedPortionTop > (window.innerHeight / 2)) {
                            // Do nothing
                        }

                        // Scroll to the section top
                        else {
                            scrollTo = sectionScrollTop;
                        }
                    }

                    // Over half the section has been scrolled

                    else {

                        // Some of the section content is below the fold, so if we scroll then that content can never be accessed
                        if (clippedPortionBottom) {
                            // Do nothing
                        }

                        // Scroll to section bottom
                        else {
                            scrollTo = sectionScrollBottom;
                        }
                    }

                    if (scrollTo !== null) {
                        SCROLL.LOCK.scrolling = true;
                        SCROLL.LOCK.$scroll.animate({scrollTop: scrollTo + 1}, SCROLL.LOCK.scrollSpeed);

                        setTimeout(function () {
                            SCROLL.LOCK.scrolling = false;
                        }, SCROLL.LOCK.scrollSpeed + 50);
                    }

                }, 500);
            }
        }

    };

    (function ($) {
        $(document).ready(function () {
            SCROLL.init();
        });
    })(jQuery);

})();
