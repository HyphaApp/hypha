(function () {
    "use strict";

    let submission_arrow = document.createElement("span");
    submission_arrow.classList.add("arrow");

    let submission_toggle = document.createElement("button");
    submission_toggle.classList.add(
        "all-submissions-table__toggle",
        "js-toggle-submission"
    );
    submission_toggle.setAttribute("title", "Show submission details");
    submission_toggle.appendChild(submission_arrow);

    // Add the toggle arrow before the submission titles.
    const submission_titles = document.querySelectorAll(
        ".all-submissions-table__parent > td.title"
    );
    submission_titles.forEach(function (title) {
        title.prepend(submission_toggle.cloneNode(true));
    });

    // Show/hide the submission child rows.
    const children = document.querySelectorAll(".js-toggle-submission");
    children.forEach(function (child) {
        child.addEventListener("click", (e) => {
            e.target
                .closest(".all-submissions-table__parent")
                .classList.toggle("is-expanded");
        });
    });
})();
