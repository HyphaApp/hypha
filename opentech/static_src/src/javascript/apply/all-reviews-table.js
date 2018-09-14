(function ($) {

    'use strict';

    // Allow click and drag scrolling within reviews table wrapper
    $('.js-reviews-table').attachDragger();

    // Enable click and drag scrolling within a div
    $.fn.attachDragger = function(){
        let attachment = false, lastPosition, position, difference;
        $($(this).selector ).on('mousedown mouseup mousemove', (e) => {
            if(e.type == 'mousedown') attachment = true, lastPosition = [e.clientX, e.clientY];
            if(e.type == 'mouseup') attachment = false;
            if(e.type == 'mousemove' && attachment == true ){
                position = [e.clientX, e.clientY];
                difference = [ (position[0]-lastPosition[0]), (position[1]-lastPosition[1])];
                $(this).scrollLeft( $(this).scrollLeft() - difference[0]);
                $(this).scrollTop( $(this).scrollTop() - difference[1]);
                lastPosition = [e.clientX, e.clientY];
            }
        });
        $(window).on('mouseup', () => attachment = false);
    };

})(jQuery);
