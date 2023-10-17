(function ($) {
    "use strict";

    const var_repeat = $("#id_does_not_repeat");

    if (!var_repeat.length) {
        return;
    }

    if (var_repeat[0].checked) {
        $(".form__group--report-every").hide();
        $(".form__group--schedule").hide();
    }

    var_repeat.addEventListener("click", function () {
        if (var_repeat.checked) {
            $(".form__group--report-every").hide();
            $(".form__group--schedule").hide();
        } else {
            $(".form__group--report-every").show();
            $(".form__group--schedule").show();
        }
    });
})(jQuery);
