(function ($) {

    'use strict';

    $('#deliverables').on('change', function (e) {
        e.preventDefault();
        var $selected = $(this).find('option:selected');
        $('.available-to-invoice').find('.availablequantity').remove();
        var availabletoinvoice = $selected.data('availabletoinvoice');
        if (availabletoinvoice) {
            $('.available-to-invoice').append('<b class="availablequantity">' + availabletoinvoice + '</b>');
        }
    });

    $('#add-deliverables').on('submit', function (event) {
        event.preventDefault();

        var $form = $(this);
        var projectid = $form.data('projectid');
        var invoiceid = $form.data('invoiceid');
        var deliverableid = $('#deliverables').val();
        var quantity = $form.find('input[name="quantity"]').val();
        if (!quantity) {
            quantity = 1
        }
        $.ajax({
            url: '/api/v1/projects/' + projectid + '/invoices/' + invoiceid + '/deliverables/',
            type: 'POST',
            data: {id: deliverableid, quantity: quantity},
            success: function (json) {
                $('#list-deliverables').find('.deliverables').remove();
                $('#list-deliverables').find('.total').remove();
                var deliverables = $('<div class="deliverables"></div>')
                var deliverable_items = json.deliverables
                $.each(deliverable_items, function(i) {
                    console.log(deliverable_items[i]['deliverable']['name'], deliverable_items[i]['deliverable']['unit_price'], deliverable_items[i]['quantity']);
                    var deliverable = $('<b>' + deliverable_items[i]['deliverable']['name'] + ' (' + deliverable_items[i]['quantity'] + ' $' + deliverable_items[i]['deliverable']['unit_price'] + ')</b><a href="remove"> Remove</a><br>');
                    $(deliverables).append(deliverable);
                    console.log('===');
                });
                $('#list-deliverables').append(deliverables);
                console.log(json.total);
                var total = $('<div class="total"><b>...</b><br><b>Total: $' + json.total + '</b></div>');
                $('#list-deliverables').append(total);
            },
            error: function (json) {
                console.log('error');
                console.log(json);
            }
        });
    });
    $('#list-deliverables').on('click', 'a', function(event) { 
        event.preventDefault();
        $.ajax({
            url: $(this).attr('href'),
            type: 'DELETE',
            success: function(json) {
                $('#list-deliverables').find('.deliverables').remove();
                $('#list-deliverables').find('.total').remove();
                var deliverables = $('<div class="deliverables"></div>')
                var deliverable_items = json.deliverables
                $.each(deliverable_items, function(i) {
                    console.log(deliverable_items[i]['deliverable']['name'], deliverable_items[i]['deliverable']['unit_price'], deliverable_items[i]['quantity']);
                    var deliverable = $('<b>' + deliverable_items[i]['deliverable']['name'] + ' (' + deliverable_items[i]['quantity'] + ' $' + deliverable_items[i]['deliverable']['unit_price'] + ')</b><a href="remove"> Remove</a><br>');
                    $(deliverables).append(deliverable);
                    console.log('===');
                });
                $('#list-deliverables').append(deliverables);
                console.log(json.total);
                var total = $('<div class="total"><b>...</b><br><b>Total: $' + json.total + '</b></div>');
                $('#list-deliverables').append(total);
            }
        });
    });
})(jQuery);
