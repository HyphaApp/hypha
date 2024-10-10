"use strict";

(function ($) {
    function add_update_events() {
        $(".message_type").each(function () {
            var message_type = $(this);
            var textarea = message_type
                .siblings(".email_message")
                .find("textarea");
            var select = message_type.find("select");
            if (!select.attr("evented")) {
                select.attr("evented", true);
                select.change(function () {
                    var message_id = $(this).val();
                    var message = $(
                        ".messaging_help_panel [attr-email-id='" +
                            message_id +
                            "']"
                    )
                        .text()
                        .trim();
                    textarea.val(message);
                });
            }
        });
    }

    $(function () {
        $("#id_messaging_settings-ADD").click(function () {
            add_update_events();
        });
        add_update_events();
    });
})(jQuery);
