(function ($) {
    $(document).ready(function formReady() {
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
