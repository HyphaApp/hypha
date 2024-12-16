(function () {
  htmx.on("translatedSubmission", (event) => {
    if (event.detail?.appTitle) {
      document.getElementById("app-title").textContent = event.detail.appTitle;
    }

    if (event.detail?.docTitle) {
      document.title = event.detail.docTitle;
    }
  });
})();
