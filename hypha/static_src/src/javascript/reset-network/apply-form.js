/* eslint-env jquery */

(function () {

    'use strict';

    var APPLY_FORM = {

        init: function () {
            var $applyForm = $('.apply-form');
            var $richTextFirst = $applyForm.find('.rich-text').first();
            var $formGroupFirst = $applyForm.find('.form__group').first();

            if (!$richTextFirst.length) {
                return;
            }

            if (!$formGroupFirst.length) {
                APPLY_FORM.removeHeaderMargin($richTextFirst);
            }
            else if ($richTextFirst.offset().top < $formGroupFirst.offset().top) {
                APPLY_FORM.removeHeaderMargin($richTextFirst);
            }
        },

        removeHeaderMargin: function ($richText) {
            var $firstItem = $richText.children().first();
            var tag = $firstItem[0].tagName;

            if (tag === 'H1' || tag === 'H2' || tag === 'H3' || tag === 'H4' || tag === 'H5' || tag === 'H6') {
                $firstItem.css('margin-top', 0);
            }
        }
    };

    (function ($) {
        $(document).ready(function () {
            APPLY_FORM.init();
        });
    })(jQuery);

})();
