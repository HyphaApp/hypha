import jQuery from './globals';
import MobileMenu from './components/mobile-menu';
import Search from './components/search';
import MobileSearch from './components/mobile-search';
import Tabs from './components/tabs';
import '@fancyapps/fancybox';

(function ($) {
    $(document).ready(function(){
        // remove no-js class if js is enabled
        document.querySelector('html').classList.remove('no-js');

        $(MobileMenu.selector()).each((index, el) => {
            new MobileMenu($(el), $('.js-mobile-menu-close'), $('.header__menus--mobile'), $('.header__search'));
        });

        $(Search.selector()).each((index, el) => {
            new Search($(el), $('.header__search'));
        });

        $(MobileSearch.selector()).each((index, el) => {
            new MobileSearch($(el), $('.header__menus--mobile'), $('.header__search'), $('.js-search-toggle'));
        });

        $(Tabs.selector()).each((index, el) => {
            new Tabs($(el));
        });

        // Show list of selected files for upload on input[type=file]
        $('input[type=file]').change(function() {
            // remove any existing files first
            $(this).siblings('.form__file').remove();
            for (let i = 0; i < $(this)[0].files.length; ++i) {
                $(this).parents('.form__item').prepend(`
                    <p class="form__file">${$(this)[0].files[i].name}</p>
                `);
            }
        });

        // Show actions sidebar on mobile
        $('.js-actions-toggle').click(function(e) {
            e.preventDefault();
            this.classList.toggle('is-active');
            this.nextElementSibling.classList.toggle('is-visible');
        });

        // Fancybox global options
        $('[data-fancybox]').fancybox({
            animationDuration : 350,
            animationEffect : 'fade'
        });

        // Open the activity feed
        $('.js-open-feed').click((e) => {
            e.preventDefault();
            $('body').addClass('no-scroll');
            $('.js-activity-feed').addClass('is-open');
        });

        // Close the activity feed
        $('.js-close-feed').click((e) => {
            e.preventDefault();
            $('body').removeClass('no-scroll');
            $('.js-activity-feed').removeClass('is-open');
        });

        // Show scroll to top of activity feed button on scroll
        $('.js-activity-feed').on('scroll', function() {
            $(this).scrollTop() === 0 ? $('.js-to-top').removeClass('is-visible') : $('.js-to-top').addClass('is-visible');
        });

        // Scroll to the top of the activity feed
        $('.js-to-top').click(() => $('.js-activity-feed').animate({ scrollTop: 0 }, 250));

        // Allow click and drag scrolling within reviews table wrapper
        $('.js-reviews-table').attachDragger();
    });

    // Add active class to filters - dropdowns are dynamically appended to the dom,
    // so we have to listen for the event higher up
    $('body').on('click', '.select2-dropdown', (e) => {
        // get the id of the dropdown
        let selectId = e.target.parentElement.parentElement.id;

        // find the matching dropdown
        let match = $(`.select2-selection[aria-owns="${selectId}"]`);

        // if the dropdown contains a clear class, the filters are active
        if($(match[0]).find('span.select2-selection__clear').length !== 0) {
            match[0].classList.add('is-active');
        } else {
            match[0].classList.remove('is-active');
        }
    });

    // remove active class on clearing select2
    $('.select2').on('select2:unselecting', (e) => {
        const dropdown = e.target.nextElementSibling.firstChild.firstChild;
        (dropdown.classList.contains('is-active')) ? dropdown.classList.remove('is-active') : null;
    });

    // open mobile filters
    $('.js-open-filters').on('click', (e) => {
        $('body').addClass('no-scroll');
        e.target.nextElementSibling.classList.add('is-open');
        $('.js-filter-list').addClass('form__filters--mobile');
    });

    // close mobile filters
    $('.js-close-filters').on('click', (e) => {
        $('body').removeClass('no-scroll');
        e.target.parentElement.parentElement.classList.remove('is-open');
        $('.js-filter-list').removeClass('form__filters--mobile');
    });

    // clear all filters
    $('.js-clear-filters').on('click', () =>{
        const dropdowns = document.querySelectorAll('.form__filters--mobile select');
        dropdowns.forEach(dropdown => {
            $(dropdown).val(null).trigger('change');
            $('.select2-selection.is-active').removeClass('is-active');
            mobileFilterPadding(dropdown);
        });
    });

    function mobileFilterPadding (element) {
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

    // reset mobile filters if they're open past the tablet breakpoint
    $(window).resize(function resize(){
        if ($(window).width() < 768) {
            $('.select2').on('click', (e) => {
                mobileFilterPadding(e.target);
            });
        } else {
            $('body').removeClass('no-scroll');
            $('.js-filter-wrapper').removeClass('is-open');
            $('.js-filter-list').removeClass('form__filters--mobile');
            $('.js-actions-toggle').removeClass('is-active');
            $('.js-actions-sidebar').removeClass('is-visible');
        }
    }).trigger('resize');
})(jQuery);

// wait for DOM content to load before checking for select2
document.addEventListener('DOMContentLoaded', () => {
    // Add active class to select2 checkboxes after page has been filtered
    const clearButtons = document.querySelectorAll('.select2-selection__clear');
    clearButtons.forEach(clearButton => {
        clearButton.parentElement.parentElement.classList.add('is-active');
    });
});
