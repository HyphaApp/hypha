class Tabs {
    static selector() {
        return '.js-tabs';
    }

    constructor() {
        // The tabs
        this.tabItems = Array.prototype.slice.call(document.querySelectorAll('.tab__item:not(.js-tabs-off)'));

        // The tabs content
        this.tabsContents = Array.prototype.slice.call(document.querySelectorAll('.tabs__content'));

        // Active classes
        this.tabActiveClass = 'tab__item--active';
        this.tabContentActiveClass = 'tabs__content--current';
        this.defaultSelectedTab = 'tab-1';
        this.bindEvents();
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
        this.stripTabClasses();

        const tab = e.currentTarget;

        this.addTabClasses(tab);
    }

    stripTabClasses(){
        // remove active classes from all tabs and tab contents
        this.tabItems.forEach(tabItem => tabItem.classList.remove(this.tabActiveClass));
        this.tabsContents.forEach(tabsContent => tabsContent.classList.remove(this.tabContentActiveClass));
    }

    addTabClasses(tab){
        if(tab === null) {
            tab = document.querySelector(`[data-tab=${this.defaultSelectedTab}]`);
        }

        const tabId = tab.getAttribute('data-tab');

        // add active classes to tabs and their respecitve content
        tab.classList.add(this.tabActiveClass);
        document.querySelector(`#${tabId}`).classList.add(this.tabContentActiveClass);
    }
}

export default Tabs;
