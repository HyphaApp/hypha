class Tabs {
    static selector() {
        return '.js-tabs';
    }

    constructor() {
        this.bindEvents();
    }

    bindEvents() {
        // Create an array first, so forEach will work in IE11
        const tabItems = Array.prototype.slice.call(document.querySelectorAll('.tab__item'));

        tabItems.forEach((el) => {
            el.addEventListener('click', (e) => {
                // prevent the page jumping
                e.preventDefault();
                this.tabs(e);
            });
        });
    }

    tabs(e) {
        // Find current target
        const toggle = e.currentTarget;

        // Tab id is set in data-tab in html
        const tabid = toggle.getAttribute('data-tab');

        // Class to apply to active items
        const activeClassItem = 'tab__item--active';
        const activeClassContent = 'tabs__content--current';

        // Remove all existing .current
        const tabItems = Array.prototype.slice.call(document.querySelectorAll('.tab__item'));
        tabItems.forEach(el => el.classList.remove(activeClassItem));
        const tabsContent = Array.prototype.slice.call(document.querySelectorAll('.tabs__content'));
        tabsContent.forEach(el => el.classList.remove(activeClassContent));

        // Add current class
        toggle.classList.add(activeClassItem);
        document.querySelector(`#${tabid}`).classList.add(activeClassContent);
    }
}

export default Tabs;
