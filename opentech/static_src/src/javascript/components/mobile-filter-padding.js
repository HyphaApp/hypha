import $ from './../globals';

export default function mobileFilterPadding (element) {
    const expanded = 'expanded-filter-element';
    const dropdown = $(element).closest('.select2');
    const openDropdown = $('.select2 .' + expanded);
    let dropdownMargin = 0;

    if(openDropdown.length > 0 && !openDropdown.hasClass('select2-container--open')){
            // reset the margin of the select we previously worked
        openDropdown.removeClass(expanded);
            // store the offset to adjust the new select box (elements above the old dropdown unaffected)
        if (dropdown.position().top > openDropdown.position().top ){
            dropdownMargin = parseInt(openDropdown.css('marginBottom'));
        }
        openDropdown.css('margin-bottom', '0px');
    }

    if(dropdown.hasClass('select2-container--open')){
        dropdown.addClass(expanded);
        const dropdownID = $(element).closest('.select2-selection').attr('aria-owns');
            // Element which has the height of the select dropdown
        const match = $(`ul#${dropdownID}`);
        const dropdownHeight = match.outerHeight(true);

            // Element which has the position of the dropdown
        const positionalMatch = match.closest('.select2-container');

            // Pad the bottom of the select box
        dropdown.css('margin-bottom', `${dropdownHeight}px`);

            // bump up the dropdown options by height of closed elements
        positionalMatch.css('top', positionalMatch.position().top - dropdownMargin);
    }
}
