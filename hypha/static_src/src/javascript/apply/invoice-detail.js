(function ($) {

    'use strict';

    function init() {
        // Set on page load
        var valid_checks = $("input[name='valid_checks']");
        if(valid_checks){
            hide_invoice_change_status();
        }

    }

    function hide_invoice_change_status() {
        var valid_checks = $("input[name='valid_checks']:checked").val();
        var update_invoice_status = document.getElementById('update_invoice_status');

        if( ! $("input[name='valid_checks']").prop('checked') ){
            $(update_invoice_status).addClass('button--tooltip-disabled');  
            $(update_invoice_status).attr('data-tooltip', "Only clickable when providing information for required checks");  
        }
    }

    $("input[name='valid_checks']").change((e) => {
        e.preventDefault();
        if($("input[name='valid_checks']").prop('checked')){
            $(update_invoice_status).removeClass('button--tooltip-disabled');  
            $(update_invoice_status).attr('data-tooltip', "Change Invoice Status");  
        }else{
            $(update_invoice_status).addClass('button--tooltip-disabled');  
            $(update_invoice_status).attr('data-tooltip', "Only clickable when providing information for required checks");  
        }
    });

    init();

})(jQuery);
