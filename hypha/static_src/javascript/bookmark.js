(function ($) {
    "use strict";

    $(".bookmarked-table")
        .find(".all-submissions-table__parent")
        .each(function () {
            var $bookmarked_item = $(this);
            var submission_id = $bookmarked_item.data("record-id");
            var bookmark_type = $bookmarked_item.data("bookmark-type");
            var $button =
                '<span class="button--float"><button class="button button--bookmark button--unbookmark bookmarked" data-id="' +
                submission_id +
                '" data-type="' +
                bookmark_type +
                '">bookmark</button></span>';
            $bookmarked_item
                .find("td.comments")
                .css("position", "relative")
                .append($button);
        });

    $(".button--bookmark").on("click", function (e) {
        e.preventDefault();

        var $current = $(this);
        var id = $current.data("id");
        var type = $current.data("type");

        $.ajax({
            url: "/apply/submissions/" + id + "/" + type + "/bookmark/",
            type: "POST",
            success: function (json) {
                if (json.result) {
                    $current.addClass("bookmarked");
                } else {
                    $current.removeClass("bookmarked");
                }
            },
        });
    });
})(jQuery);
