(function () {
  let wordCountInterval;

  const WARNING_THRESHOLD = 0.8;

  /**
   * Count words and manage warning states for an element
   * @param {HTMLElement} element - Target element to process
   */
  function updateWordCount(element) {
    const currentCount = parseInt(element.innerText.match(/\d+/)?.[0], 10) || 0;
    const fieldset = element.closest("[data-word-limit]");
    const limit = parseInt(fieldset.dataset.wordLimit, 10);
    const warningThreshold = limit * WARNING_THRESHOLD;
    const textCharacters = fieldset.dataset.wordCountCharacters || "characters";
    const textOutOf = fieldset.dataset.wordCountOutOf || "out of";
    const textClose = fieldset.dataset.wordCountClose || "(Close to the limit)";
    const textOver = fieldset.dataset.wordCountOver || "(Over the limit)";

    /**
     * Clear warning states and classes
     */
    function clearWarnings() {
      delete element.dataset.afterWordCount;
      element.classList.remove("word-count-warning", "word-count-warning-2");
    }

    if (element.textContent.includes(textCharacters)) {
      clearWarnings();
      return;
    }

    element.dataset.afterWordCount = ` ${textOutOf} ${limit}`;

    if (currentCount <= warningThreshold) {
      clearWarnings();
    } else if (currentCount <= limit) {
      element.dataset.afterWordCount += ` ${textClose}`;
      element.classList.remove("word-count-warning-2");
      element.classList.add("word-count-warning");
    } else {
      element.dataset.afterWordCount += ` ${textOver}`;
      element.classList.add("word-count-warning-2");
    }
  }

  const observer = new MutationObserver((mutations) =>
    mutations.forEach((mutation) => updateWordCount(mutation.target))
  );

  /**
   * Initialize word count tracking for matching elements
   */
  function initializeWordCount() {
    const elements = document.querySelectorAll(".tox-statusbar__wordcount");

    if (elements.length) {
      clearInterval(wordCountInterval);
      elements.forEach((element) => {
        updateWordCount(element);
        observer.observe(element, {
          childList: true,
        });
      });
    }
  }

  wordCountInterval = setInterval(initializeWordCount, 300);
})();
