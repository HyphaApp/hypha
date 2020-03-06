/* global jQuery */
(function($) {
  $.fn.select2.amd.require(
    [
      'select2/multi-checkboxes/dropdown',
      'select2/multi-checkboxes/selection',
      'select2/multi-checkboxes/results'
    ],
    function(DropdownAdapter, SelectionAdapter, ResultsAdapter) {

      $(function () {
        $('.django-select2-checkboxes').each(function (i, element) {
          var $element = $(element)

          $element.select2({
            placeholder: $element.data('placeholder'),
            templateSelection: function(data) {
              let filterType = $element.data('placeholder');

              if (!data.selected.length) {
                return filterType
              } else if (data.selected.length == data.all.length ) {
                return 'All ' + filterType + ' selected';
              }
              return data.selected.length + ' of ' + data.all.length + ' ' + filterType + ' selected';
            },
            selectionAdapter: SelectionAdapter,
            resultsAdapter: ResultsAdapter
          });

        });
      });
    }
  );
}(this.jQuery));