function formContents(f) {
    "use strict";
    // Thanks to https://stackoverflow.com/a/44033425
    return Array.from(new FormData(f), function (e) {
        return e.map(encodeURIComponent).join("=");
    }).join("&");
}

document.addEventListener("DOMContentLoaded", function () {
    "use strict";
    const form = document.getElementById("review-form-edit");
    const original = formContents(form);

    window.onbeforeunload = function () {
        const formNow = formContents(form);
        if (formNow !== original) {
            return "Are you sure you want to leave?";
        }
    };

    form.addEventListener("submit", function () {
        window.onbeforeunload = null;
    });
});
