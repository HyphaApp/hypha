(function ($) {
  // add the require attribute to the field configs
  function addRequiredToKey(fields, findKey) {
    $.each(fields, (index, value) => {
      var fieldName = Object.keys(value)[0];
      var data = value[fieldName];
      if (fieldName === findKey) {
        data.required = true;
      } else if (Array.isArray(data)) {
        // Handle nested fields
        addRequiredToKey(data, findKey);
      }
    });
  }

  // hook into the transform to update with the required attribute
  var oldTransform = $.fn.addressfield.transform;
  $.fn.addressfield.transform = function (data) {
    var mappedData = oldTransform.call(this, data);
    $.each(mappedData, (key, value) => {
      $.each(value.required, (index, field) => {
        addRequiredToKey(mappedData[key].fields, field);
      });
    });
    return mappedData;
  };

  function labelFor(field) {
    var fieldId = $(field).attr("id");
    var label = $('label[for="' + fieldId + '"]');
    return label;
  }

  function makeFieldNotRequired(field) {
    var $field = $(field);
    $field.removeAttr("required");
    var $label = labelFor($field);
    $label.children("span").remove();
  }

  function makeFieldRequired(field) {
    var $field = $(field);
    $field.prop("required", true);
    var $label = labelFor($field);
    $label.append('<span class="form__required">*</span>');
  }

  // Hook into the validate process to update the required display
  var oldValidate = $.fn.addressfield.validate;
  $.fn.addressfield.validate = function (field, config) {
    if (config.required) {
      makeFieldRequired(this);
    } else {
      makeFieldNotRequired(this);
    }
    oldValidate.call(this, field, config);
  };

  // Hook into the select builder to update the display
  var oldConvertToSelect = $.fn.addressfield.convertToSelect;
  $.fn.addressfield.convertToSelect = function () {
    var $select = oldConvertToSelect.call(this);
    $select.wrap('<div class="form__select"></div>');
    return $select;
  };

  // Hook into the text builder to update the display
  var oldConvertToText = $.fn.addressfield.convertToText;
  $.fn.addressfield.convertToText = function () {
    var $text = oldConvertToText.call(this);
    $text.unwrap();
    return $text;
  };

  $(document).ready(function formReady() {
    $(".form .address").each(function () {
      var config = {
        json: "/static/addressfield.min.json",
        fields: {
          country: "[data-js-addressfield-name='country']",
          thoroughfare: "[data-js-addressfield-name='thoroughfare']",
          premise: "[data-js-addressfield-name='premise']",
          locality: "[data-js-addressfield-name='locality']",
          localityname: "[data-js-addressfield-name='localityname']",
          administrativearea:
            "[data-js-addressfield-name='administrativearea']",
          postalcode: "[data-js-addressfield-name='postalcode'] ",
        },
      };
      $(".form div#" + this.id).addressfield(config);
    });
  });
})(jQuery);
