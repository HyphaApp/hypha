(function ($) {
    // On document ready, instantiate the plugin.
    $(document).ready(function formReady() {
        // Initialize jquery.validate (optional).
        // $('#address-example').validate({});

        // Initialize jquery.addressfield.
        $('.form div.address').addressfield({
            json: '/static/addressfield.min.json',
            fields: {
                country: ".country",
                thoroughfare: ".thoroughfare",
                premise: ".premise",
                locality: ".locality",
                localityname: ".localityname",
                administrativearea: ".administrativearea",
                postalcode: ".postalcode"
            }
        });
    });
})(jQuery);
