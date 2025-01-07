const selectElements = document.querySelectorAll(".js-choices");

selectElements.forEach((selectElement) => {
  // eslint-disable-next-line no-undef
  // biome-ignore lint: undeclared
  new Choices(selectElement, {
    shouldSort: false,
    allowHTML: true,
    removeItemButton: true,
  });
});
