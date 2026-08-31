// The TinyMCE editing area is an iframe, so the page stylesheet does not reach
// it and it stays white in dark mode. Use TinyMCE's bundled dark content
// stylesheet instead.
//
// Loaded via TINYMCE_EXTRA_MEDIA, which places it after tinymce.min.js but
// before django_tinymce/init_tinymce.js, so the default is set before any
// editor is initialised.
(function () {
  /**
   * Name of the bundled content stylesheet matching the current theme.
   * @returns {string} "dark" or "default"
   */
  function contentCss() {
    const theme = document.documentElement.dataset.theme;
    const isDark =
      theme === "dark" ||
      (theme !== "light" &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);

    return isDark ? "dark" : "default";
  }

  tinymce.overrideDefaults({ content_css: contentCss() });

  /**
   * Re-point an already initialised editor at the other content stylesheet.
   *
   * Swapping the href keeps the editor alive, so the undo stack and cursor
   * position survive a theme change.
   *
   * @param {Object} editor - TinyMCE editor instance.
   * @param {string} name - "dark" or "default".
   */
  function swapContentCss(editor, name) {
    const doc = editor.getDoc?.();
    if (!doc) {
      return;
    }

    const link = Array.from(
      doc.querySelectorAll('link[rel="stylesheet"]')
    ).find((stylesheet) => stylesheet.href.includes("/skins/content/"));

    const href = `${tinymce.baseURL}/skins/content/${name}/content${tinymce.suffix}.css`;

    if (link && link.href !== href) {
      link.href = href;
    }
  }

  // An editor freezes content_css when it is constructed, but its iframe
  // document only exists once it is initialised. A theme change in between is
  // therefore invisible to both overrideDefaults and swapContentCss, so re-sync
  // every editor as it becomes ready.
  tinymce.on("AddEditor", function (event) {
    event.editor.on("init", function () {
      swapContentCss(event.editor, contentCss());
    });
  });

  // The theme toggle sets data-theme on <html>. It also re-sets the attribute
  // when the OS preference changes while in "auto" mode, so this covers both.
  new MutationObserver(function () {
    const name = contentCss();

    // Editors created from here on, e.g. by HTMX swapping in a new form.
    tinymce.overrideDefaults({ content_css: name });

    for (const editor of tinymce.get() ?? []) {
      swapContentCss(editor, name);
    }
  }).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });
})();
