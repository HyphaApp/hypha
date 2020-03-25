/* eslint-env jquery */

(function () {

    'use strict';

    var PEOPLE = {

        init: function () {
            PEOPLE.ACCORDION.init();
        },

        // *********************************************************************
        // **************************** ACCORDION ******************************
        // *********************************************************************

        ACCORDION: {

            windowWidth: null,

            init: function () {

                PEOPLE.ACCORDION.windowWidth = window.innerWidth;

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
                    if (window.innerWidth !== PEOPLE.ACCORDION.windowWidth) {
                        PEOPLE.ACCORDION.windowWidth = window.innerWidth;
                        resizeTimeout = setTimeout(PEOPLE.ACCORDION.closeAll, 500);
                    }
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


    };

    (function ($) {
        $(document).ready(function () {
            PEOPLE.init();
        });
    })(jQuery);

})();
