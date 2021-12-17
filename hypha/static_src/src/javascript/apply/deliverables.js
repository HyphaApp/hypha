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
            quantity = 1;
        }
        $.ajax({
            url: '/api/v1/projects/' + projectid + '/invoices/' + invoiceid + '/deliverables/',
            type: 'POST',
            data: {id: deliverableid, quantity: quantity},
            success: function (json) {
                $('#add-deliverables').find('.error').remove();
                $('#list-deliverables').find('.deliverables').remove();
                $('#list-deliverables').find('.total').remove();
                var deliverables = $('<div class="deliverables"></div>');
                var deliverable_items = json.deliverables;
                $.each(deliverable_items, function (i) {
                    var url = '/api/v1/projects/' + deliverable_items[i]['project_id'] + '/invoices/' + deliverable_items[i]['invoice_id'] + '/deliverables/';
                    var deliverable = $('<b>' + deliverable_items[i]['deliverable']['name'] + ' (' + deliverable_items[i]['quantity'] + ' $' + deliverable_items[i]['deliverable']['unit_price'] + ')</b><a href="' + url + deliverable_items[i]['id'] + '/"> Remove</a><br>');
                    $(deliverables).append(deliverable);
                });
                $('#list-deliverables').append(deliverables);
                if (json.total) {
                    var total = $('<div class="total"><b>...</b><br><b>Total: $' + json.total + '</b></div>');
                    $('#list-deliverables').append(total);
                }
            },
            error: function (json) {
                $('#add-deliverables').find('.error').remove();
                var errorText = $('<p class="error" style="color:red">' + json.responseJSON.detail + '</p>');
                $('#add-deliverables').append(errorText);
            }
        });
    });
    $('#list-deliverables').on('click', 'a', function (event) {
        event.preventDefault();
        $.ajax({
            url: $(this).attr('href'),
            type: 'DELETE',
            success: function (json) {
                $('#add-deliverables').find('.error').remove();
                $('#list-deliverables').find('.deliverables').remove();
                $('#list-deliverables').find('.total').remove();
                var deliverables = $('<div class="deliverables"></div>');
                var deliverable_items = json.deliverables;
                $.each(deliverable_items, function (i) {
                    var url = '/api/v1/projects/' + deliverable_items[i]['project_id'] + '/invoices/' + deliverable_items[i]['invoice_id'] + '/deliverables/';
                    var deliverable = $('<b>' + deliverable_items[i]['deliverable']['name'] + ' (' + deliverable_items[i]['quantity'] + ' $' + deliverable_items[i]['deliverable']['unit_price'] + ')</b><a href="' + url + deliverable_items[i]['id'] + '/"> Remove</a><br>');
                    $(deliverables).append(deliverable);
                });
                $('#list-deliverables').append(deliverables);
                if (json.total) {
                    var total = $('<div class="total"><b>...</b><br><b>Total: $' + json.total + '</b></div>');
                    $('#list-deliverables').append(total);
                }
            },
            error: function (json) {
                $('#add-deliverables').find('.error').remove();
                var errorText = $('<p class="error" style="color:red">' + json.responseJSON.detail + '</p>');
                $('#add-deliverables').append(errorText);
            }
        });
    });
})(jQuery);
