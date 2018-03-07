class Tabs {
    static selector() {
        return '.js-tabs';
    }

    constructor() {
        // The tabs
        this.tabItems = Array.prototype.slice.call(document.querySelectorAll('.tab__item'));

        // The tabs content
        this.tabsContents = Array.prototype.slice.call(document.querySelectorAll('.tabs__content'));

        // Active classes
        this.tabActiveClass = 'tab__item--active';
        this.tabContentActiveClass = 'tabs__content--current';
        this.bindEvents();
    }

    bindEvents() {
        // Get the current url
        const url = document.location.toString();

        // If the url contains a hash, activate the relevant tab
        if (url.match('#')) {
            this.updateTab(url);
        }

        this.tabItems.forEach((el) => {
            el.addEventListener('click', (e) => {
                // prevent the page jumping
                e.preventDefault();
                this.tabs(e);
            });
        });
    }

    updateTab(url) {
        this.stripTabClasses();

        // Find tab with matching hash and activate
        const match = document.querySelector(`a[href="#${url.split('#')[1]}"]`);
        const tabId = match.getAttribute('data-tab');

        this.addTabClasses(match, tabId);
    }

    tabs(e) {
        this.stripTabClasses();

        // Find current tab
        const tab = e.currentTarget;

        // Tab id is set in data-tab in html
        const tabId = tab.getAttribute('data-tab');

        this.addTabClasses(tab, tabId);
    }

    stripTabClasses(){
        // remove active classes from all tabs and tab contents
        this.tabItems.forEach(tabItem => tabItem.classList.remove(this.tabActiveClass));
        this.tabsContents.forEach(tabsContent => tabsContent.classList.remove(this.tabContentActiveClass));
    }

    addTabClasses(tab, tabId){
        // add active classes to tabs and their respecitve content
        tab.classList.add(this.tabActiveClass);
        document.querySelector(`#${tabId}`).classList.add(this.tabContentActiveClass);
    }
}

export default Tabs;
