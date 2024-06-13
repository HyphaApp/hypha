(function () {
    "use strict";

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
    const CLASS_JS_CONSENT_CLOSE = "js-cookieconsent-close";
    const CLASS_JS_LEARNMORE = "js-cookieconsent-show-learnmore";
    const CLASS_JS_LEARNMORE_EXPAND = `${CLASS_JS_LEARNMORE}-expand`;

    const cookieconsent = document.querySelector(`.${CLASS_COOKIECONSENT}`);
    if (!cookieconsent) return;

    const cookieButtons = cookieconsent.querySelectorAll(
        "button[data-consent]"
    );
    const learnMoreToggles = cookieconsent.querySelectorAll(
        ".button--learn-more"
    );
    const closePromptBtn = cookieconsent.querySelector(".button--close");

    const analyticsToggle = cookieconsent.querySelector(".analytics-toggle");
    if (analyticsToggle) {
        analyticsToggle.checked = getConsentValue() === ACCEPT ? true : false;
    }

    function getConsentValue() {
        return localStorage.getItem(COOKIECONSENT_KEY);
    }

    function setConsentValue(value) {
        if ([ACCEPT, DECLINE, ACK].includes(value)) {
            localStorage.setItem(COOKIECONSENT_KEY, value);
        } else {
            // If for whatever reason the value is not in the predefined values, assume decline
            localStorage.setItem(COOKIECONSENT_KEY, DECLINE);
        }
    }

    function openConsentPrompt() {
        cookieconsent.classList.add(CLASS_JS_CONSENT_OPEN);
    }

    function closeConsentPrompt() {
        cookieconsent.classList.remove(CLASS_JS_CONSENT_CLOSE);
    }

    // Expose consent prompt opening/closing globally (ie. to use in a footer)
    window.openConsentPrompt = openConsentPrompt;
    window.closeConsentPrompt = closeConsentPrompt;

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

    // Adds "tabability" to menu buttons/toggles
    function setInputTabIndex(wrapperClassSelector, tabValue) {
        const wrapper = cookieconsent.querySelector(wrapperClassSelector);
        const tabables = wrapper.querySelectorAll("button, input");
        tabables.forEach((element) => (element.tabIndex = tabValue));
    }

    // Open the prompt if consent value is undefined OR if analytics has been added since the user ack'd essential cookies
    if (
        getConsentValue() == undefined ||
        (getConsentValue() === ACK && cookieButtons.length > 1)
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

    closePromptBtn.addEventListener("click", function () {
        let consent;
        if (analyticsToggle) {
            consent = analyticsToggle.checked ? ACCEPT : DECLINE;
        } else {
            consent = ACK;
        }
        setConsentValue(consent);
        closeConsentPrompt();
    });
})();
