/*
 * Address field (vanilla JS)
 * original: https://github.com/tableau-mkt/jquery.addressfield
 *
 * Licensed under the MIT license.
 */
(() => {
  "use strict";

  // WeakMap for per-element value storage during select↔input conversion.
  const savedValues = new WeakMap();

  // --- Private helpers ---

  /** Return the <label> element for el, or null. */
  const labelFor = (el) =>
    el.id ? document.querySelector(`label[for="${el.id}"]`) : null;

  /** Trigger a change event on the country element to apply its config. */
  const trigger = (container, countrySelector) =>
    container
      .querySelector(countrySelector)
      ?.dispatchEvent(new Event("change", { bubbles: true }));

  /** Mark a specific field key as required within a fields array (recurses). */
  function addRequiredToKey(fields, findKey) {
    for (const fieldObj of fields) {
      const [fieldName, data] = Object.entries(fieldObj)[0];
      if (fieldName === findKey) {
        data.required = true;
      } else if (Array.isArray(data)) {
        addRequiredToKey(data, findKey);
      }
    }
  }

  // --- Main entry point ---

  /**
   * Initialise an address widget.
   *
   * @param {Element} container  The DOM element wrapping the address fields.
   * @param {Object}  options    Configuration: fields, json, async, defs.
   * @returns {Element} container
   */
  function addressfield(container, options = {}) {
    const configs = {
      fields: {},
      json: null,
      async: true,
      defs: { fields: {} },
      ...options,
    };

    if (typeof configs.json === "string") {
      fetch(configs.json)
        .then((res) => res.json())
        .then((data) => {
          const transformed = addressfield.transform(data);
          addressfield.initCountries(
            container,
            configs.fields.country,
            transformed
          );
          addressfield.binder(container, configs.fields, transformed);
          trigger(container, configs.fields.country);
        });
      return container;
    }

    if (configs.json !== null && typeof configs.json === "object") {
      const transformed = addressfield.transform(configs.json);
      addressfield.initCountries(
        container,
        configs.fields.country,
        transformed
      );
      addressfield.binder(container, configs.fields, transformed);
      trigger(container, configs.fields.country);
      return container;
    }

    // Legacy: apply a one-time mutation without JSON config.
    return addressfield.apply(container, configs.defs, configs.fields);
  }

  // --- Static methods ---

  /**
   * Apply a country field configuration to an address container.
   *
   * @param {Element} container
   * @param {Object}  config    Country config (has a .fields array).
   * @param {Object}  fieldMap  xNAL name → CSS selector mapping.
   * @returns {Element} container
   */
  addressfield.apply = function (container, config, fieldMap) {
    const fieldOrder = [];

    for (const fieldObj of config.fields) {
      const [field, fieldConfig] = Object.entries(fieldObj)[0];
      const selector = Object.hasOwn(fieldMap, field)
        ? fieldMap[field]
        : `.${field}`;
      let el = container.querySelector(selector);

      // Nested field group (e.g. locality containing localityname etc.)
      if (Array.isArray(fieldConfig)) {
        return addressfield.apply(
          container.querySelector(selector) ?? container,
          { fields: fieldConfig },
          fieldMap
        );
      }

      if (el && Object.hasOwn(fieldMap, field)) {
        fieldOrder.push(selector);

        if (fieldConfig.options !== undefined) {
          if (el.tagName !== "SELECT") el = addressfield.convertToSelect(el);
          addressfield.updateOptions(el, fieldConfig.options);
        } else {
          if (el.tagName === "SELECT") el = addressfield.convertToText(el);
          addressfield.updateEg(el, fieldConfig.eg ?? "");
        }

        addressfield.updateLabel(el, fieldConfig.label);
      }

      if (el && !addressfield.isVisible(el) && Object.hasOwn(fieldMap, field)) {
        addressfield.showField(el);
      }

      if (el) {
        addressfield.validate(el, field, fieldConfig);
      }
    }

    // Hide fields present in fieldMap but absent from this country config.
    for (const [fieldName, selector] of Object.entries(fieldMap)) {
      const fEl = container.querySelector(selector);
      if (fEl && !addressfield.hasField(config, fieldName)) {
        addressfield.hideField(fEl);
      }
    }

    addressfield.orderFields(container, fieldOrder);

    container.dispatchEvent(
      new CustomEvent("addressfield:after", {
        detail: { config, fieldMap },
        bubbles: true,
      })
    );

    return container;
  };

  /**
   * Populate the country <select> with options from countryMap, but only if
   * it is currently empty (no <option> children).
   */
  addressfield.initCountries = function (container, selector, countryMap) {
    const countryEl = container.querySelector(selector);
    if (!countryEl || countryEl.options.length > 0) return;

    const defaultCountry = countryEl
      .getAttribute("data-country-selected")
      ?.toLowerCase();

    for (const [iso, country] of Object.entries(countryMap)) {
      const option = document.createElement("option");
      option.value = iso;
      option.textContent = country.label;
      if (defaultCountry && iso.toLowerCase() === defaultCountry) {
        option.selected = true;
      }
      countryEl.appendChild(option);
    }
  };

  /**
   * Bind a change handler to the country field so that selecting a country
   * applies the corresponding address field configuration.
   */
  addressfield.binder = function (container, fieldMap, countryConfigMap) {
    container
      .querySelector(fieldMap.country)
      ?.addEventListener("change", function () {
        addressfield.apply(container, countryConfigMap[this.value], fieldMap);
      });
    return container;
  };

  /**
   * Transform the raw JSON (options array) into a map keyed by ISO country code,
   * and mark fields listed in country.required as required.
   */
  addressfield.transform = function (data) {
    const countryMap = Object.fromEntries(data.options.map((e) => [e.iso, e]));
    for (const country of Object.values(countryMap)) {
      if (country.required && country.fields) {
        for (const field of country.required) {
          addRequiredToKey(country.fields, field);
        }
      }
    }
    return countryMap;
  };

  /** Return whether a config contains a given field name (recurses into arrays). */
  addressfield.hasField = function (config, expectedField) {
    for (const fieldObj of config.fields) {
      const [field, data] = Object.entries(fieldObj)[0];
      if (Array.isArray(data)) {
        if (addressfield.hasField({ fields: data }, expectedField)) return true;
      } else if (field === expectedField) {
        return true;
      }
    }
    return false;
  };

  /** Update the <label> associated with el. */
  addressfield.updateLabel = function (el, label) {
    const labelEl = labelFor(el) ?? el.previousElementSibling;
    if (labelEl) labelEl.textContent = label;
  };

  /** Set or clear the placeholder hint on an input. */
  addressfield.updateEg = function (el, example) {
    el.setAttribute("placeholder", example ? `e.g. ${example}` : "");
  };

  /** Replace the <select>'s options with new ones, restoring the previous value. */
  addressfield.updateOptions = function (el, options) {
    const oldVal = savedValues.get(el) ?? el.value;
    el.innerHTML = "";
    for (const optObj of options) {
      const [value, label] = Object.entries(optObj)[0];
      const option = document.createElement("option");
      option.value = value;
      option.textContent = label;
      el.appendChild(option);
    }
    el.value = oldVal;
    el.dispatchEvent(new Event("change", { bubbles: true }));
    savedValues.delete(el);
  };

  /** Replace a <select> with a plain text <input>, unwrapping from .form__select if present. */
  addressfield.convertToText = function (el) {
    const input = document.createElement("input");
    input.type = "text";
    addressfield.copyAttrsTo(el, input);
    input.value = el.value;
    el.replaceWith(input);
    const parent = input.parentNode;
    if (parent?.classList.contains("form__select")) {
      parent.replaceWith(input);
    }
    return input;
  };

  /** Replace a text <input> with a <select> wrapped in .form__select, saving the old value. */
  addressfield.convertToSelect = function (el) {
    const select = document.createElement("select");
    addressfield.copyAttrsTo(el, select);
    savedValues.set(select, el.value);
    el.replaceWith(select);
    const wrapper = document.createElement("div");
    wrapper.className = "form__select";
    select.replaceWith(wrapper);
    wrapper.appendChild(select);
    return select;
  };

  /** Update the required attribute and label indicator based on field config. */
  addressfield.validate = function (el, _field, config) {
    const label = labelFor(el);
    if (config.required) {
      el.setAttribute("required", "");
      if (label && !label.querySelector(".form__required")) {
        const span = document.createElement("span");
        span.className = "form__required";
        span.textContent = "*";
        label.appendChild(span);
      }
    } else {
      el.removeAttribute("required");
      label?.querySelector(".form__required")?.remove();
    }
  };

  /** Hide a field and its container. */
  addressfield.hideField = function (el) {
    el.value = "";
    el.style.display = "none";
    const c = addressfield.container(el);
    if (c) c.style.display = "none";
  };

  /** Show a field and its container. */
  addressfield.showField = function (el) {
    el.style.display = "";
    const c = addressfield.container(el);
    if (c) c.style.display = "";
  };

  /** Return true if el is currently visible in the layout. */
  addressfield.isVisible = (el) =>
    el.offsetParent !== null && el.style.display !== "none";

  /**
   * Return the nearest ancestor element that contains the label for el.
   * Falls back to el.parentElement.
   */
  addressfield.container = function (el) {
    if (!el) return null;
    const labelEl = labelFor(el) ?? el.previousElementSibling;
    let parent = el.parentElement;
    while (parent) {
      if (labelEl && parent.contains(labelEl)) return parent;
      parent = parent.parentElement;
    }
    return el.parentElement;
  };

  /** Copy a safe subset of attributes (class, id, name) from src to dst. */
  addressfield.copyAttrsTo = function (src, dst) {
    for (const attr of ["class", "id", "name"]) {
      const val = src.getAttribute(attr);
      if (val !== null) dst.setAttribute(attr, val);
    }
  };

  /** Re-order field containers within container to match the given selector order. */
  addressfield.orderFields = function (container, order) {
    const fieldContainers = order
      .map((selector) => {
        const el = container.querySelector(selector);
        return el ? addressfield.container(el) : null;
      })
      .filter(Boolean);

    for (const c of fieldContainers) c.remove();
    for (const c of fieldContainers) container.appendChild(c);
  };

  // --- Initialisation ---

  const FIELDS = {
    country: "[data-js-addressfield-name='country']",
    thoroughfare: "[data-js-addressfield-name='thoroughfare']",
    premise: "[data-js-addressfield-name='premise']",
    locality: "[data-js-addressfield-name='locality']",
    localityname: "[data-js-addressfield-name='localityname']",
    administrativearea: "[data-js-addressfield-name='administrativearea']",
    postalcode: "[data-js-addressfield-name='postalcode']",
  };

  document.addEventListener("DOMContentLoaded", () => {
    for (const container of document.querySelectorAll(".form .address")) {
      addressfield(container, {
        json: "/static/addressfield.min.json",
        fields: FIELDS,
      });
    }
  });
})();
