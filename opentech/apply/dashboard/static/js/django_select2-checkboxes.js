(function ($) {
  $(function () {
      $('.django-select2-checkboxes').select2MultiCheckboxes({
          templateSelection: function(selected, total) {
              let filterType = 'Placeholder';
              if ( !selected.length ) {
                  return filterType;
              } else if ( selected.length===total ) {
                  return 'All ' + filterType + ' selected';
              }
              return selected.length + ' of ' + total + ' selected';
          }
      });
  });
}(this.jQuery));
