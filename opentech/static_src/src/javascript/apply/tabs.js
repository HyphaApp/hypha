(function ($) {

    'use strict';

    let Tabs = class {
        static selector() {
            return '.js-tabs';
        }

        constructor(node) {
            this.node = node[0];
            // The tabs
            this.tabItems = Array.prototype.slice.call(this.node.querySelectorAll('.tab__item:not(.js-tabs-off)'));

            // The tabs content
            this.tabsContents = Array.prototype.slice.call(document.querySelectorAll('.tabs__content'));

            // The tabs content container
            this.tabsContentsContainer = Array.prototype.slice.call(document.querySelectorAll('.js-tabs-content'));

            // Active classes
            this.tabActiveClass = 'tab__item--active';
            this.tabContentActiveClass = 'tabs__content--current';
            this.defaultSelectedTab = 'tab-1';
            this.addDataAttributes();
            this.bindEvents();
        }

        addDataAttributes() {
            // Add data-attrs for multiple tabs
            this.tabsContentsContainer.forEach((tabsContent, i) => {
                tabsContent.dataset.tabs = i + 1;
            });

            $('.js-tabs').each(function (i) {
                $(this).attr('data-tabs', i + 1);
            });
        }

        bindEvents() {
            this.updateTabOnLoad();

            this.tabItems.forEach((el) => {
                el.addEventListener('click', (e) => {
                    // prevent the page jumping
                    e.preventDefault();
                    this.tabs(e);
                });
            });
        }

        findTab(href) {
            return document.querySelector(`a[href="#${href}"]`);
        }

        updateTabOnLoad() {
            // Find tab with matching hash and activate
            const url = document.location.toString();
            const match = this.findTab(url.split('#')[1]);

            this.addTabClasses(match);
        }

        tabs(e) {
            // Find current tab
            const tab = e.currentTarget;

            const tabContentId = $(tab).closest('.js-tabs').data('tabs');
            this.stripTabClasses(tabContentId);
            this.addTabClasses(tab);
            this.updateUrl(tab);
        }

        stripTabClasses(tabContentId) {
            // remove active classes from all tabs and tab contents
            const parents = Array.prototype.slice.call($(`.js-tabs-content[data-tabs=${tabContentId}]`).find('.tabs__content'));
            const childTabs = Array.prototype.slice.call($(`.js-tabs[data-tabs=${tabContentId}]`).find('.tab__item'));
            childTabs.forEach(tabItem => tabItem.classList.remove(this.tabActiveClass));
            parents.forEach(tabsContent => tabsContent.classList.remove(this.tabContentActiveClass));
        }

        addTabClasses(tab) {
            if (tab === null) {
                tab = document.querySelector(`[data-tab=${this.defaultSelectedTab}]`);
            }

            const tabId = tab.getAttribute('data-tab');
            const tabContentId = $(tab).closest('.js-tabs').data('tabs');
            const parents = $(`.js-tabs-content[data-tabs=${tabContentId}]`);

            // add active classes to tabs and their respecitve content
            tab.classList.add(this.tabActiveClass);
            $(parents).find(`#${tabId}`).addClass(this.tabContentActiveClass);
        }

        updateUrl(tab) {
            window.location.hash = tab.getAttribute('href');
        }
    };

    $(Tabs.selector()).each((index, el) => {
        new Tabs($(el));
    });

})(jQuery);
