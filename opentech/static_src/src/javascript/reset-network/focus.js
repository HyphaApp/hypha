/* eslint-env jquery */

(function () {

    'use strict';

    var FOCUS = {
        element: document.body,
        restrictedTypes: ['mouse', 'touch'],
        restrictClass: 'focus-disabled',
        inputType: 'mouse',
        interactLock: false,
        init: function init() {
            FOCUS.element.addEventListener('mousedown', FOCUS.interact);
            FOCUS.element.addEventListener('touchstart', FOCUS.interact);
            FOCUS.element.addEventListener('keydown', FOCUS.interact);
            FOCUS.element.addEventListener('focus', FOCUS.preFocus, true);
            FOCUS.element.addEventListener('blur', FOCUS.preBlur, true);
        },
        interact: function interact(e) {
            if (!FOCUS.interactLock) {
                switch (e.type) {
                    case 'mousedown':
                        FOCUS.interactLock = false;
                        FOCUS.inputType = 'mouse';
                        break;
                    case 'touchstart':
                        FOCUS.interactLock = true;
                        FOCUS.inputType = 'touch';
                        break;
                    default:
                    case 'keydown':
                        FOCUS.inputType = 'keyboard';
                        break;
                }
            }
        },
        preFocus: function preFocus() {
            for (var i = 0; i < FOCUS.restrictedTypes.length; i++) {
                if (FOCUS.inputType === FOCUS.restrictedTypes[i]) {
                    FOCUS.addClass(FOCUS.element, FOCUS.restrictClass);
                    break;
                }
            }
        },
        preBlur: function preBlur() {
            FOCUS.removeClass(FOCUS.element, FOCUS.restrictClass);
        },
        hasClass: function hasClass(el, className) {
            return new RegExp(' ' + className + ' ').test(' ' + el.className + ' ');
        },
        addClass: function addClass(el, className) {
            if (!FOCUS.hasClass(el, className)) {
                el.className += ' ' + className;
            }
        },
        removeClass: function removeClass(el, className) {
            var newClass = ' ' + el.className.replace(/[\t\r\n]/g, ' ') + ' ';
            if (FOCUS.hasClass(el, className)) {
                while (newClass.indexOf(' ' + className + ' ') >= 0) {
                    newClass = newClass.replace(' ' + className + ' ', ' ');
                }
                el.className = newClass.replace(/^\s+|\s+$/g, '');
            }
        }
    };

    (function ($) {
        $(document).ready(function () {
            FOCUS.init();
        });
    })(jQuery);

})();
