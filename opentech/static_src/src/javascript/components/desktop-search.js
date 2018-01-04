class DesktopSearch {
    static selector() {
        return '.js-desktop-search-toggle';
    }

    constructor(node, searchForm) {
        this.node = node;
        this.searchForm = searchForm;
        this.bindEventListeners();
    }

    bindEventListeners() {
        this.node.click(this.toggle.bind(this));
    }

    toggle() {
        this.searchForm[0].classList.toggle('is-visible');
        this.node[0].querySelector('.header__icon--magnifying-glass').classList.toggle('is-hidden');
        this.node[0].querySelector('.header__icon--cross').classList.toggle('is-unhidden');
    }
}

export default DesktopSearch;
