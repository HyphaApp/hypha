(function ($) {
    var oldTransform = $.fn.addressfield.transform;
    $.fn.addressfield.transform = function(data) {
        var mappedData = oldTransform.call(this, data);
        return mappedData;
    };

    $('.form').bind('addressfield:after', function (e, data) {
        debugger;
    });

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
