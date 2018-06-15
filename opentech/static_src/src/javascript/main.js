import jQuery from './globals';
import MobileMenu from './components/mobile-menu';
import Search from './components/search';
import MobileSearch from './components/mobile-search';
import Tabs from './components/tabs';
import listInputFiles from './components/list-input-files';
import toggleActionsPanel from './components/toggle-actions-panel';
import activityFeed from './components/activity-feed';
import fancyboxGlobal from './components/fancybox-global';
import allSubmissions from './components/all-submissions-table';
import allReviews from './components/all-reviews-table';
import submissionFilters from './components/submission-filters';
import mobileFilterPadding from './components/mobile-filter-padding';

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
        listInputFiles();

        // Show actions sidebar on mobile
        toggleActionsPanel();

        // Global fancybox options
        fancyboxGlobal();

        // Activity feed functionality
        activityFeed();

        // Submissions overview table logic
        allSubmissions();


        // Add colspan and accordion classes to review table header table rows
        const accordionTableHeaders = $('.table--reviews tr th:only-child');
        accordionTableHeaders.each((val, accordionHeader) => {
            $(accordionHeader).attr('colspan', 100);
            $(accordionHeader).parent('tr').addClass('js-accordion__toggle');
        });

        // Cache accordion items
        const $jsAccordionToggle = $('.js-accordion__toggle');

        // Add hidden classes to js-accordion items
        $jsAccordionToggle.nextUntil('.js-accordion__toggle').addClass('is-hidden');

        // Toggle accordion items
        $jsAccordionToggle.click(function() {
            if($(this).hasClass('is-expanded')){
                $(this).removeClass('is-expanded');
                $(this).nextUntil('.js-accordion__toggle').addClass('is-hidden');
                return;
            }
            $('.js-accordion__toggle.is-expanded').nextUntil('.js-accordion__toggle').addClass('is-hidden');
            $(this).addClass('is-expanded');
            $(this).nextUntil('.js-accordion__toggle').removeClass('is-hidden');
        });
    });

        // All reviews table logic
        allReviews();

        // Submission filters logic
        submissionFilters();
    });

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
            $('.tr--parent.is-expanded').removeClass('is-expanded');
        }
    }).trigger('resize');
})(jQuery);
