(function ($) {
    "use strict";

    $(".thumb").on("click", function (e) {
        e.preventDefault();

        var $current = $(this);
        var id = $current.data("id");
        var yes = $current.data("yes");

        $.ajax({
            url: "/api/v1/submissions/" + id + "/screening_statuses/default/",
            type: "POST",
            data: { yes: yes },
            success: function (json) {
                if (json) {
                    var screeningOptions = $(
                        '<p id="screening-options-para">' +
                            '<a id="screening-options-ajax" data-fancybox="" data-src="#screen-application" data-yes=' +
                            yes +
                            ' class="link link--secondary-change" href="#"> Screening Options</a></p>'
                    );
                    if (
                        $.trim(
                            $(".show-screening-options")
                                .find("#screening-options-para")
                                .html()
                        ) === ""
                    ) {
                        $(".show-screening-options").find("#Options").remove();
                        $(".show-screening-options")
                            .find("#screening-options")
                            .remove();
                    }
                    $(".show-screening-options")
                        .find("#screening-options-para")
                        .remove();
                    $(".show-screening-options").append(screeningOptions);
                    if (yes === true) {
                        $(".js-dislike").removeClass(
                            "button--js-dislike-active"
                        );
                        $current
                            .find("button")
                            .addClass("button--js-like-active");
                    } else {
                        $(".js-like").removeClass("button--js-like-active");
                        $current
                            .find("button")
                            .addClass("button--js-dislike-active");
                    }
                }
            },
        });
    });

    $(".show-screening-options").on(
        "click",
        "#screening-options-ajax",
        function () {
            var $screeningOptions = $(this);
            var currentStatus = $screeningOptions.data("yes");
            var $screenApplication = $("#screen-application");
            var yesStatuses = $screenApplication.data("yes-statuses");
            var noStatuses = $screenApplication.data("no-statuses");
            var defaultYes = $screenApplication.data("default-yes");
            var defaultNo = $screenApplication.data("default-no");
            var $screeningStatuses = $screenApplication.find(
                "#id_screening_statuses"
            );
            $screeningStatuses = $screeningStatuses.empty();
            if (currentStatus === true) {
                $("#current-status").text("Current decisions: " + defaultYes);
                $.each(yesStatuses, function (key, value) {
                    if (key === defaultYes) {
                        $screeningStatuses.append(
                            $("<option></option>")
                                .attr("value", value)
                                .attr("selected", "selected")
                                .text(key)
                        );
                    } else {
                        $screeningStatuses.append(
                            $("<option></option>")
                                .attr("value", value)
                                .text(key)
                        );
                    }
                });
            } else {
                $("#current-status").text("Current decisions: " + defaultNo);
                $.each(noStatuses, function (key, value) {
                    if (key === defaultNo) {
                        $screeningStatuses.append(
                            $("<option></option>")
                                .attr("value", value)
                                .attr("selected", "selected")
                                .text(key)
                        );
                    } else {
                        $screeningStatuses.append(
                            $("<option></option>")
                                .attr("value", value)
                                .text(key)
                        );
                    }
                });
            }
        }
    );
})(jQuery);
