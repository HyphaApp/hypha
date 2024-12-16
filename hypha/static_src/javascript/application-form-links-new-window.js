(function () {
  // Make links on application forms open in a new window/tab.
  const links = document.querySelectorAll(".application-form a");
  links.forEach(function (link) {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });
})();
