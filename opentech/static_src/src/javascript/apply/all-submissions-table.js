(function ($) {

    'use strict';

    // add the toggle arrow before the submission titles
    $('.all-submissions-table__parent td.title').prepend('<span class="all-submissions-table__toggle js-toggle-submission"><span class="arrow"></span></span>');

    // grab all the toggles
    const children = Array.prototype.slice.call(
        document.querySelectorAll('.js-toggle-submission')
    );

    // show/hide the submission child rows
    children.forEach(function (child) {
        child.addEventListener('click', (e) => {
            $(e.target).closest('.all-submissions-table__parent').toggleClass('is-expanded');
        });
    });

})(jQuery);
