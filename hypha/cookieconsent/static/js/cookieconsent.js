(function () {
  const ACCEPT = "accept";
  const DECLINE = "decline";
  const ACK = "ack"; // Only for essential cookies

  const COOKIECONSENT_KEY = "cookieconsent";

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

  document.addEventListener("alpine:init", () => {
    Alpine.data("cookieConsent", () => ({
      isOpen: false,
      showLearnMore: false,

      init() {
        const consentValue = getConsentValue();
        const cookieButtons = this.$el.querySelectorAll("button[data-consent]");

        // Open the prompt if consent value is undefined OR if analytics has been added since the user ack'd essential cookies
        if (
          consentValue == null ||
          (consentValue === ACK && cookieButtons.length > 2)
        ) {
          this.openConsentPrompt();
        }

        cookieButtons.forEach((button) => {
          button.addEventListener("click", () => {
            const buttonValue = button.getAttribute("data-consent");
            this.handleConsent(buttonValue);
          });
        });

        // Expose methods globally for external use (ie. footer links)
        window.openConsentPrompt = () => this.openConsentPrompt();
        window.closeConsentPrompt = () => this.closeConsentPrompt();
      },

      openConsentPrompt() {
        this.isOpen = true;
        this.showLearnMore = false;
      },

      closeConsentPrompt() {
        this.isOpen = false;
        this.showLearnMore = false;
      },

      handleConsent(value) {
        setConsentValue(value);
        this.closeConsentPrompt();
      },

      toggleLearnMore() {
        this.showLearnMore = !this.showLearnMore;
      },
    }));
  });
})();
