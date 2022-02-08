(function ($) {

    'use strict';

    $('#required-checks').on('submit', function (event) {
        event.preventDefault();

        var $form = $(this);
        var projectid = $form.data('projectid');
        var invoiceid = $form.data('invoiceid');
        var validChecks = $form.find('input[type=checkbox]').prop('checked');
        var validChecksLink = $form.find('textarea[name="valid-checks-link"]').val();
        console.log(validChecks);
        console.log(validChecksLink);
        $.ajax({
            url: '/api/v1/projects/' + projectid + '/invoices/' + invoiceid + '/set_required_checks/',
            type: 'POST',
            data: {valid_checks: validChecks, valid_checks_link: validChecksLink},
            success: function (json) {
                $('#required-checks').find('.message').remove();
                var successText = $('<span class="message" style="color:green">' + 'Successfully saved!' + '</span>');
                $('#required-checks').append(successText);
            },
            error: function (json) {
                $('#required-checks').find('.message').remove();
                if (json.responseJSON.valid_checks_link) {
                    var errorText1 = $('<span class="message" style="color:red">' + json.responseJSON.valid_checks_link + '</span>');
                    $('#required-checks').append(errorText1);
                }
                else if (json.responseJSON.valid_checks) {
                    var errorText2 = $('<span class="message" style="color:red">' + json.responseJSON.valid_checks + '</span>');
                    $('#required-checks').append(errorText2);
                }
                else {
                    var errorText3 = $('<span class="message" style="color:red">' + 'Server Error' + '</span>');
                    $('#required-checks').append(errorText3);
                }
            }
        });
    });
})(jQuery);
