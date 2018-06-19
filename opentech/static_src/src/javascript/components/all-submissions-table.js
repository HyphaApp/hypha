import $ from './../globals';

export default () => {
    // Add <tr> toggle arrow
    $('.all-submissions__parent td.title').prepend('<span class="js-tr-toggle arrow"></span>');

    // Toggle show/hide for submissions overview table rows
    const children = Array.prototype.slice.call(
        document.querySelectorAll('.js-tr-toggle')
    );

    children.forEach(function (child) {
        child.addEventListener('click', (e) => {
            $(e.target).closest('.all-submissions__parent').toggleClass('is-expanded');
        });
    });
};
