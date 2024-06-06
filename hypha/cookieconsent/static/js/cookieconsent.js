(function () {
    "use strict";

    // Used when an analytics cookie notice is enabled
    const ACCEPT = "accept";
    const DECLINE = "decline";
    // Used when only essential cookies are in use
    const ACK = "ack";

    const COOKIECONSENT_KEY = "cookieconsent";

    const cookieconsent = document.querySelector(".cookieconsent");
    if (!cookieconsent) return;

    const cookie_buttons = cookieconsent.querySelectorAll(
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
        cookieconsent.classList.add("js-cookieconsent-open");
    }

    function closeConsentPrompt() {
        cookieconsent.classList.remove("js-cookieconsent-open");
    }

    // Expose consent prompt opening/closing globally (ie. to use in a footer to configure options later)
    window.openConsentPrompt = openConsentPrompt;
    window.closeConsentPrompt = closeConsentPrompt;

    // open the prompt if consent value is undefined OR if analytics has been added since the user ack'd essential cookies
    if (
        getConsentValue() == undefined ||
        (getConsentValue() === ACK && cookie_buttons.length > 1)
    ) {
        openConsentPrompt();
    }

    cookie_buttons.forEach(function (button) {
        button.addEventListener("click", function () {
            const buttonValue = button.getAttribute("data-consent");
            setConsentValue(buttonValue);
            closeConsentPrompt();
        });
    });

    learnMoreToggles.forEach(function (button) {
        button.addEventListener("click", function () {
            const buttonValue = button.getAttribute("show-learn-more");
            const content = cookieconsent.querySelector(
                ".cookieconsent__content"
            );
            if (buttonValue === "true") {
                content.classList.add("js-cookieconsent-show-learnmore");
                cookieconsent.classList.add(
                    "js-cookieconsent-show-learnmore-expand"
                );
            } else {
                content.classList.remove("js-cookieconsent-show-learnmore");
                cookieconsent.classList.remove(
                    "js-cookieconsent-show-learnmore-expand"
                );
            }
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
