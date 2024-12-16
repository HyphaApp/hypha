(function ($) {
  // Visibility Index is set to 0 initially in the backend. But in case of edit application forms
  // with multiple values already set, we need to update it. The visibility index helps
  // to get the next field from the list of hidden inputs to be shown to an applicant on clicking the add button.
  // For example, a total of 5 multiple inputs, 3 values are already set by applicant while creating a submission.
  // On edit form, the visibility index should be updates so when the user clicks add, the 4th input should be displayed.
  $(".multi-input-add-btn").each(function () {
    var multiFieldId = $(this).data("multi-field-id");
    const multiMaxIndex = $(this).data("multi-max-index");
    var multiFieldInputs = $(
      ".form__item[data-multi-field-for='" + multiFieldId + "']"
    );
    var multiFieldHiddenInput = $(
      ".form__item.multi-input-field-hidden[data-multi-field-for='" +
        multiFieldId +
        "']"
    );
    var multiVisibilityIndex = multiFieldInputs.index(multiFieldHiddenInput);
    if (multiVisibilityIndex >= 0) {
      $(this).data("multi-visibility-index", multiVisibilityIndex);
    } else if (multiVisibilityIndex === -1) {
      $(this).data("multi-visibility-index", multiMaxIndex);
    }
  });

  $(".multi-input-add-btn").click(function () {
    var multiFieldId = $(this).data("multi-field-id");
    var multiVisibilityIndex = $(this).data("multi-visibility-index");
    const multiMaxIndex = $(this).data("multi-max-index");

    var multiShowIndex = multiVisibilityIndex + 1;
    if (multiShowIndex <= multiMaxIndex) {
      var multiShowId = "id_" + multiFieldId + "_" + multiShowIndex;
      $("#" + multiShowId)
        .parent(".form__item")
        .removeClass("multi-input-field-hidden");
      $(this).data("multi-visibility-index", multiShowIndex);
    } else {
      $(this).hide();
    }
  });
})(jQuery);
