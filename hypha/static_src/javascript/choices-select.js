const selectElements = document.querySelectorAll('.js-choices');

selectElements.forEach(selectElement => {
    // eslint-disable-next-line no-undef
    new Choices(selectElement, {
        shouldSort: false,
        allowHTML: true,
        removeItemButton: true,
    });
});
