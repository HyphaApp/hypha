(function () {
    "use strict";

    const related_sidebar = document.querySelector(".related-sidebar");
    const content_height = related_sidebar
        .querySelector("ul")
        .getBoundingClientRect().height;

    let button_show = document.createElement("button");
    button_show.classList.add("button", "button--primary", "button--narrow");
    button_show.textContent = "Show";

    let button_wrapper = document.createElement("p");
    button_wrapper.classList.add("related-sidebar__show-button");
    button_wrapper.appendChild(button_show);

    if (content_height > 300) {
        related_sidebar.classList.add("related-sidebar--collaps");
        related_sidebar.append(button_wrapper);
    }

    button_show.addEventListener("click", function (e) {
        related_sidebar.classList.remove("related-sidebar--collaps");
        button_wrapper.remove();
    });
})();
