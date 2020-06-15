(function ($) {

    'use strict';

    $('.multi-input-add-btn').each(function () {
        var multiFieldId = $(this).data('multi-field-id');
        const multiMaxIndex = $(this).data('multi-max-index');
        var multiFieldInputs = $(".form__item[data-multi-field-for='" + multiFieldId + "']");
        var multiFieldHiddenInput = $(".form__item.multi-input-field-hidden[data-multi-field-for='" + multiFieldId + "']");
        var multiVisibilityIndex = multiFieldInputs.index(multiFieldHiddenInput);
        if (multiVisibilityIndex >= 0) {
            $(this).data('multi-visibility-index', multiVisibilityIndex);
        }
        else if (multiVisibilityIndex == -1) {
            $(this).data('multi-visibility-index', multiMaxIndex);
        }
    });

    $('.multi-input-add-btn').click(function () {
        var multiFieldId = $(this).data('multi-field-id');
        var multiVisibilityIndex = $(this).data('multi-visibility-index');
        const multiMaxIndex = $(this).data('multi-max-index');

        var multiShowIndex = multiVisibilityIndex + 1;
        if (multiShowIndex <= multiMaxIndex) {
            var multiShowId = 'id_' + multiFieldId + '_' + multiShowIndex;
            $('#' + multiShowId).parent('.form__item').removeClass('multi-input-field-hidden');
            $(this).data('multi-visibility-index', multiShowIndex);
        }
        else {
            $(this).hide();
        }
    });
})(jQuery);
