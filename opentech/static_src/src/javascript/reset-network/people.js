/* eslint-env jquery */

(function () {

    'use strict';

    var PEOPLE = {

        init: function () {
            PEOPLE.ACCORDION.init();
            PEOPLE.HOVER.init();
        },

        // *********************************************************************
        // **************************** ACCORDION ******************************
        // *********************************************************************

        ACCORDION: {

            init: function () {
                $('.js-person .person__title').on('click', function () {
                    var $this = $(this);
                    var $person = $this.closest('.js-person');

                    if ($person.hasClass('is-active')) {
                        PEOPLE.ACCORDION.close($person);
                    }
                    else {
                        PEOPLE.ACCORDION.open($person);
                    }
                });

                var resizeTimeout = null;
                window.addEventListener('resize', function () {
                    clearTimeout(resizeTimeout);
                    resizeTimeout = setTimeout(PEOPLE.ACCORDION.closeAll, 500);
                });
            },

            open: function ($person) {
                var $lvl1 = $person.find('.person__tray');
                var height = $person.find('.person__info-wrap').outerHeight();

                $person.addClass('is-active');
                $lvl1.css('height', height + 'px');
            },

            close: function ($person) {
                var $lvl1 = $person.find('.person__tray');

                $person.removeClass('is-active');
                $lvl1.css('height', 0);
            },

            closeAll: function () {
                var $people = $('.js-person');

                for (var i = 0; i < $people.length; i++) {
                    PEOPLE.ACCORDION.close($($people[i]));
                }
            }
        },

        // *********************************************************************
        // ***************************** HOVER *********************************
        // *********************************************************************

        // On hover of people images have the person's avatar follow the cursor
        HOVER: {

            $people: null,
            $targets: null,
            $currImg: null,
            offsetX: null,
            offsetY: null,

            init: function () {

                // Don't permit cursor follow on touch devices
                if ('ontouchstart' in document.documentElement) {
                    return;
                }

                PEOPLE.HOVER.$people = $('.js-person');
                PEOPLE.HOVER.$targets = $('.js-person-target');

                PEOPLE.HOVER.$targets.mouseenter(function (e) {
                    PEOPLE.HOVER.bind($(this), e.clientX, e.clientY);
                });

                PEOPLE.HOVER.$targets.mouseleave(PEOPLE.HOVER.unBind);
            },

            bind: function ($target, x, y) {
                PEOPLE.HOVER.reset();

                PEOPLE.HOVER.$people.addClass('is-person-hovered');
                $target.closest('.js-person').addClass('is-hovered');

                PEOPLE.HOVER.onMove($target, x, y);
                $target.on('mousemove', function (e) {
                    PEOPLE.HOVER.onMove($target, e.clientX, e.clientY);
                });
            },

            unBind: function () {
                PEOPLE.HOVER.reset();
            },

            onMove: function ($target, x, y) {
                requestAnimationFrame(function () {
                    var $currImg = PEOPLE.HOVER.currImg || $target.find('.js-img');
                    var offsetX = PEOPLE.HOVER.offsetX || $target.offset().left;
                    var offsetY = PEOPLE.HOVER.offsetY || $target.offset().top - window.scrollY;
                    var imgLeft = x - offsetX;
                    var imgRight = y - offsetY;

                    $currImg.css({
                        transform: 'translate(calc(-50% + ' + imgLeft + 'px), calc(-50% + ' + imgRight + 'px))'
                    });
                });
            },

            reset: function () {
                PEOPLE.HOVER.$people.removeClass('is-hovered is-person-hovered');
                PEOPLE.HOVER.$targets.off('mousemove');

                PEOPLE.HOVER.$currImg = null;
                PEOPLE.HOVER.offsetX = null;
                PEOPLE.HOVER.offsetY = null;
                PEOPLE.HOVER.requestFrameID = null;
            }
        }

    };

    (function ($) {
        $(document).ready(function () {
            PEOPLE.init();
        });
    })(jQuery);

})();
