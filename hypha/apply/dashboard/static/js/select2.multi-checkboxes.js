/**
 * jQuery Select2 Multi checkboxes
 * - allow to select multi values via normal dropdown control
 *
 * author      : wasikuss
 * repo        : https://github.com/wasikuss/select2-multi-checkboxes/tree/amd
 * inspired by : https://github.com/select2/select2/issues/411
 * License     : MIT
 */

/* global define jQuery */
(function(factory) {
  if (typeof define === 'function' && define.amd) {
    define(['jquery'], factory);
  } else {
    // Browser globals
    factory(jQuery);
  }
}(function(jQuery) {
  if (jQuery && jQuery.fn && jQuery.fn.select2 && jQuery.fn.select2.amd) {
    define = jQuery.fn.select2.amd.define;
  }
  var define;

  /* global define */
  define('select2/multi-checkboxes/dropdown', [
    'select2/utils',
    'select2/dropdown',
    'select2/dropdown/search',
    'select2/dropdown/attachBody'
  ],
  function(Utils, Dropdown, DropdownSearch, AttachBody) {
    return Utils.Decorate(
      Utils.Decorate(
        Dropdown,
        DropdownSearch
      ),
      AttachBody
    );
  });


  /* global define */
  define('select2/multi-checkboxes/results', [
    'jquery',
    'select2/utils',
    'select2/results'
  ],
  function($, Utils, _Results) {
    function Results() {
      Results.__super__.constructor.apply(this, arguments);
    }
    Utils.Extend(Results, _Results);

    Results.prototype.highlightFirstItem = function() {
      this.ensureHighlightVisible();
    };

    Results.prototype.bind = function(container) {
      container.on('open', function() {
        var $options = this.$results.find('.select2-results__option[aria-selected]');
        var $selected = $options.filter('[aria-selected=true]');
        var $optionToScrollTo = ($selected.length > 0 ? $selected : $selected).first();
        $optionToScrollTo.trigger('mouseenter');
      });
      Results.__super__.bind.apply(this, arguments);
    };

    Results.prototype.template = function(result, container) {
      var template = this.options.get('templateResult');
      var escapeMarkup = this.options.get('escapeMarkup');

      var content = template(result, container);
      $(container).addClass('multi-checkboxes_wrap');

      if (content == null) {
        container.style.display = 'none';
      } else if (typeof content === 'string') {
        container.innerHTML = escapeMarkup(content);
      } else {
        $(container).append(content);
      }
    };

    return Results;
  });


  /* global define */
  define('select2/multi-checkboxes/selection', [
    'select2/utils',
    'select2/selection/multiple',
    'select2/selection/placeholder',
    'select2/selection/single',
    'select2/selection/eventRelay'
  ],
  function(Utils, MultipleSelection, Placeholder, SingleSelection, EventRelay) {
    var adapter = Utils.Decorate(MultipleSelection, Placeholder);
    adapter = Utils.Decorate(adapter, EventRelay);

    adapter.prototype.render = function() {
      return SingleSelection.prototype.render.call(this);
    };

    adapter.prototype.update = function(data) {
      var $rendered = this.$selection.find('.select2-selection__rendered');
      var formatted = '';

      if (data.length === 0) {
        formatted = this.options.get('placeholder') || '';
      } else {
        var itemsData = {
          selected: data || [],
          all: this.$element.find('option') || []
        };
        formatted = this.display(itemsData, $rendered);
      }

      $rendered.empty().append(formatted);
      $rendered.prop('title', formatted);
    };

    return adapter;
  });
})
);
