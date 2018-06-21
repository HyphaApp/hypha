import $ from './../globals';

export default () => {
    // add the toggle arrow before the submission titles
    $('.all-submissions__parent td.title').prepend('<span class="all-submissions__toggle js-toggle-submission"><span class="arrow"></span></span>');

    // grab all the toggles
    const children = Array.prototype.slice.call(
        document.querySelectorAll('.js-toggle-submission')
    );

    // show/hide the submission child rows
    children.forEach(function (child) {
        child.addEventListener('click', (e) => {
            $(e.target).closest('.all-submissions__parent').toggleClass('is-expanded');
        });
    });
};
