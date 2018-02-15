(function ($) {
    var init = function ($element) {
        options = {
            placeholder: $element.data('placeholder'),
            templateSelection: function(selected, total) {
                let filterType = this.placeholder;
                if ( !selected.length ) {
                    return filterType;
                } else if ( selected.length===total ) {
                    return 'All ' + filterType + ' selected';
                }
                return selected.length + ' of ' + total + ' selected';
            }
        };
        $element.select2MultiCheckboxes(options);
    };
    $(function () {
        $('.django-select2-checkboxes').each(function (i, element) {
            var $element = $(element);
            init($element);
        });
    });
}(this.jQuery));
