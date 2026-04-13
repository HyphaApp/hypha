(function () {
  "use strict";

  /**
   * Strip HTML tags from a string and return plain text.
   * @param {string} html
   * @returns {string}
   */
  function strip(html) {
    const el = document.createElement("div");
    el.innerHTML = html;
    return el.textContent.trim();
  }

  /**
   * Collect all questions and user input from the form as a Markdown string.
   * @returns {string}
   */
  function getQuestions() {
    const lines = [];
    let sectionIndex = 1;

    const h1 = document.querySelector("h1");
    if (h1) lines.push("# " + h1.textContent.trim());

    if (!applicationForm) return lines.join("\n\n");

    applicationForm
      .querySelectorAll(".form__group, h2, h3")
      .forEach(function (el) {
        let questionText = "";
        const labelEl = el.querySelector(".form__question");

        if (labelEl) {
          // Form field: build label + help + answer
          const labelText = strip(labelEl.innerHTML)
            .replace(/[\r\n]+/g, " ")
            .replace(/ {2,}/g, " ");
          questionText = "### " + labelText;

          const helpEl = el.querySelector(".form__help");
          if (helpEl) {
            questionText += "\n\n" + strip(helpEl.innerHTML);
          }

          const wordLimit = el.dataset.wordLimit;
          if (wordLimit) {
            questionText += "\n\nLimit this field to " + wordLimit + " words.";
          }

          const listItems = el.querySelectorAll(".form__list > li");
          const inputEl = el.querySelector("input");
          const richTextEl = el.querySelector(".tinymce4-editor");

          console.log(listItems);

          if (listItems.length) {
            const itemTexts = Array.from(listItems).map(function (li) {
              let text = strip(li.innerHTML);
              console.log(text);
              if (li.querySelector("input:checked")) text += " (selected)";
              return text;
            });
            questionText += "\n\n" + itemTexts.join("\n");
          } else if (inputEl && inputEl.value) {
            questionText += "\n\n" + strip(inputEl.value);
          } else if (richTextEl && richTextEl.value) {
            questionText += "\n\n" + strip(richTextEl.value);
          }
        } else {
          // Heading or markup block
          questionText = strip(el.innerHTML);
          if (el.tagName === "H2" || el.tagName === "H3") {
            questionText = "## " + sectionIndex + ". " + questionText;
            sectionIndex++;
          }
        }

        lines.push(questionText);
      });

    return lines.join("\n\n");
  }

  function handleCopy() {
    const text = getQuestions();

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(flashForm);
    } else {
      console.warn("Clipboard API not available.");
    }
  }

  function flashForm() {
    applicationForm.classList.add("animate-flash");
    setTimeout(function () {
      applicationForm.classList.remove("animate-flash");
    }, 1200);
  }

  const applicationForm = document.querySelector(".application-form");
  if (!applicationForm) return;

  // Create the copy button
  const button = document.createElement("button");
  button.textContent = "Copy questions to clipboard";
  button.className = "btn btn-secondary btn-outline w-full sm:btn-sm sm:w-auto";
  button.title =
    "Copies all the questions and user input to the clipboard in plain text.";
  button.type = "button";
  button.addEventListener("click", handleCopy);

  // Insert a copy above the form (aligned to the right)
  const topButton = button.cloneNode(true);
  topButton.classList.add("block", "ms-auto");
  topButton.addEventListener("click", handleCopy);
  applicationForm.parentNode.insertBefore(topButton, applicationForm);

  // Insert a copy after the last button inside the form
  const allButtons = applicationForm.querySelectorAll("button");
  const lastButton = allButtons.length
    ? allButtons[allButtons.length - 1]
    : null;
  if (lastButton) {
    lastButton.insertAdjacentElement("afterend", button);
  } else {
    applicationForm.appendChild(button);
  }
})();
