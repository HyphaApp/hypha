class MobileMenu {
    static selector() {
        return '.js-mobile-menu-toggle';
    }

    constructor(node, openCb = () => {}, closeCb = () => {}) {
        this.node = node;

        // Any callbacks to be called on open or close.
        this.openCb = openCb;
        this.closeCb = closeCb;

        this.state = {
            open: false,
        };

        this.bindEventListeners();
    }

    bindEventListeners() {
        this.node.click(this.toggle.bind(this));
    }

    toggle() {
        this.state.open ? this.close() : this.open();
    }

    open() {
        this.node.addClass('is-open');
        this.openCb();

        this.state.open = true;
    }

    close() {
        this.node.removeClass('is-open');
        this.closeCb();

        this.state.open = false;
    }
}

export default MobileMenu;
