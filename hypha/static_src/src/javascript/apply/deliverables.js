(function ($) {

    'use strict';

    $('#deliverables').on('change', function(e) {
        e.preventDefault();
        var $selected = $(this).find('option:selected')
        var availabletoinvoice = $selected.data('availabletoinvoice');
        $('.available-to-invoice').append('<b>' + availabletoinvoice + '</b>');
    });

    $("#add-deliverables").on('submit', function(event) {
        event.preventDefault();
    
        var $form = $(this);
        console.log('coming here');
        // url = $form.attr('action');

        /* Send the data using post with element id name and name2*/
        // var posting = $.post(url, {
        // name: $('#name').val(),
        // name2: $('#name2').val()
        // });
    
        // /* Alerts the results */
        // posting.done(function(data) {
        // $('#result').text('success');
        // });
        // posting.fail(function() {
        // $('#result').text('failed');
        // });
    });
})(jQuery);
