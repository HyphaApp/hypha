(function ($) {
    // On document ready, instantiate the plugin.
    $(document).ready(function formReady() {
        // Initialize jquery.validate (optional).
        // $('#address-example').validate({});

        // Initialize jquery.addressfield.
        $('.form div.address').addressfield({
            json: '/static/addressfield.min.json',
            fields: {
                country: "[name='country']",
                thoroughfare: "[name='address_1']",
                premise: "[name='address_2']",
                locality: "[name='locality']",
                localityname: "[name='city']",
                administrativearea: "[name='state']",
                postalcode: "[name='zip']"
            }
        });
    });
})(jQuery);
