(function () {
  // Used when an analytics cookie notice is enabled
  const ACCEPT = "accept";
  const DECLINE = "decline";
  const ACK = "ack"; // Only for essential cookies

  // Constant key used for localstorage
  const COOKIECONSENT_KEY = "cookieconsent";

  // Class constants
  const CLASS_COOKIECONSENT = "cookieconsent";
  const CLASS_LEARNMORE = "cookieconsent__learnmore";
  const CLASS_COOKIEBRIEF = "cookieconsent__brief";
  const CLASS_COOKIECONTENT = "cookieconsent__content";
  const CLASS_JS_CONSENT_OPEN = "js-cookieconsent-open";
  const CLASS_JS_LEARNMORE = "js-cookieconsent-show-learnmore";
  const CLASS_JS_LEARNMORE_EXPAND = `${CLASS_JS_LEARNMORE}-expand`;

  const cookieconsent = document.querySelector(`.${CLASS_COOKIECONSENT}`);
  if (!cookieconsent) {
    return;
  }

  const cookieButtons = cookieconsent.querySelectorAll("button[data-consent]");
  const learnMoreToggles = cookieconsent.querySelectorAll(
    ".button--learn-more"
  );

  /**
   * Pull the cookie consent value from localStorage
   *
   * @returns {(string|null)} A string if consent value exists, null if not
   */
  function getConsentValue() {
    return localStorage.getItem(COOKIECONSENT_KEY);
  }

  /**
   * Set the cookie consent value in localStorage
   *
   * @param {("accept"|"decline"|"ack")} value - consent value to set
   */
  function setConsentValue(value) {
    if ([ACCEPT, DECLINE, ACK].includes(value)) {
      localStorage.setItem(COOKIECONSENT_KEY, value);
    } else {
      // If for whatever reason the value is not in the predefined values, assume decline
      localStorage.setItem(COOKIECONSENT_KEY, DECLINE);
    }
  }

  /**
   * Trigger the cookie consent prompt to open
   */
  function openConsentPrompt() {
    cookieconsent.classList.add(CLASS_JS_CONSENT_OPEN);
  }

  /**
   * Trigger cookie consent prompt to close
   */
  function closeConsentPrompt() {
    cookieconsent.classList.remove(CLASS_JS_CONSENT_OPEN);
  }

  // Expose consent prompt opening/closing globally (ie. to use in a footer)
  window.openConsentPrompt = openConsentPrompt;
  window.closeConsentPrompt = closeConsentPrompt;

  /**
   * Trigger the "Learn More" prompt on the cookie banner to open/close
   *
   * @param {boolean} open - true to open learn more prompt, false to close
   */
  function toggleLearnMore(open) {
    const content = cookieconsent.querySelector(`.${CLASS_COOKIECONTENT}`);
    if (open) {
      content.classList.add(CLASS_JS_LEARNMORE);
      cookieconsent.classList.add(CLASS_JS_LEARNMORE_EXPAND);
    } else {
      content.classList.remove(CLASS_JS_LEARNMORE);
      cookieconsent.classList.remove(CLASS_JS_LEARNMORE_EXPAND);
    }
    setInputTabIndex(`.${CLASS_LEARNMORE}`, open ? 0 : -1);
    setInputTabIndex(`.${CLASS_COOKIEBRIEF}`, open ? -1 : 0);
  }

  /**
   * Adds "tabability" to menu buttons/toggles
   *
   * @param {string} wrapperClassSelector - wrapper class to set tabability of inputs on
   * @param {number} tabValue - tab index value to set on all input items in the wrapper class
   */
  function setInputTabIndex(wrapperClassSelector, tabValue) {
    const wrapper = cookieconsent.querySelector(wrapperClassSelector);
    const tabables = wrapper.querySelectorAll("button, input");
    tabables.forEach((element) => (element.tabIndex = tabValue));
  }

  // Open the prompt if consent value is undefined OR if analytics has been added since the user ack'd essential cookies
  if (
    getConsentValue() == null ||
    (getConsentValue() === ACK && cookieButtons.length > 2)
  ) {
    openConsentPrompt();
  }

  cookieButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const buttonValue = button.getAttribute("data-consent");
      setConsentValue(buttonValue);
      closeConsentPrompt();
    });
  });

  learnMoreToggles.forEach(function (button) {
    button.addEventListener("click", function () {
      const buttonValue = button.getAttribute("show-learn-more");
      toggleLearnMore(buttonValue === "true");
    });
  });
})();
