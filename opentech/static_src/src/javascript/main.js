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
import generateTooltips from './components/submission-tooltips';
import DeterminationCopy from './components/determination-template';
import toggleReviewers from './components/toggle-reviewers';

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

        $(DeterminationCopy.selector()).each((index, el) => {
            new DeterminationCopy($(el));
        });

        // Add tooltips to truncated titles on submissions overview table
        generateTooltips();

        // Show list of selected files for upload on input[type=file]
        listInputFiles();

        // Show actions sidebar on mobile
        toggleActionsPanel();

        // Global fancybox options
        fancyboxGlobal();

        // Activity feed logic
        activityFeed();

        // Submissions overview table logic
        allSubmissions();

        // All reviews table logic
        allReviews();

        // Submission filters logic
        submissionFilters();

        // Toggle all reviewers in the sidebar
        toggleReviewers();
    });

    // Add active class to select2 checkboxes after page has been filtered
    document.addEventListener('DOMContentLoaded', () => {
        // If there are clear buttons in the dom, it means the filters have been applied
        const clearButtons = document.querySelectorAll('.select2-selection__clear');
        clearButtons.forEach(clearButton => {
            clearButton.parentElement.parentElement.classList.add('is-active');
        });
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
