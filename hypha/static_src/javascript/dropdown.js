(function ($) {
    // Add 'data-dropdown-target' attr to dropdown button in html and set its value as id of the dropdown content.
    // For example look at its usage in project_simplified_detail.html

    "use strict";

    var dropdownButton = $("[data-dropdown-target]");
    dropdownButton.on("click", function () {
        // toggle 'show' class whenever dropdown button is getting clicked
        $($(this).attr("data-dropdown-target")).toggleClass("show");
    });

    // Close the dropdown menu if the user clicks outside of it
    window.addEventListener("click", function (event) {
        if (!event.target.matches("[data-dropdown-target]")) {
            $(dropdownButton.attr("data-dropdown-target")).removeClass("show");
        }
    });
})(jQuery);
