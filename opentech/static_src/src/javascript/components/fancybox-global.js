import $ from './../globals';
import '@fancyapps/fancybox';

export default () => {
    $('[data-fancybox]').fancybox({
        animationDuration : 350,
        animationEffect : 'fade',
        afterClose: function(){
            $('.django-select2-checkboxes').select2('close');
        }
    });

    // Close any open select2 dropdowns when inside a modal
    $('.modal').click((e) => {
        if(e.target.classList.contains('select2-selection__rendered')) return;
        $('.django-select2-checkboxes').select2('close');
    });
};
