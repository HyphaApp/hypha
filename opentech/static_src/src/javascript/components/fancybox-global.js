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
};
