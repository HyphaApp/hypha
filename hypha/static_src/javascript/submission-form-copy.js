(function () {
  "use strict";

  /**
   * Strip HTML tags from a string and return plain text.
   * @param {string} html
   * @returns {string}
   */
  function strip(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    return doc.body.textContent.trim() || "";
  }

  /**
   * Collect all questions and user input from the form as a Markdown string.
   * @returns {string}
   */
  function getQuestions() {
    var lines = [];
    var sectionIndex = 1;

    var h1 = document.querySelector("h1");
    if (h1) lines.push("# " + h1.innerHTML);

    var form = document.querySelector(".application-form");
    if (!form) return lines.join("\n\n");

    form
      .querySelectorAll(".form__group, .rich-text, h2, h3")
      .forEach(function (el) {
        var questionText = "";
        var labelEl = el.querySelector(".form__question");

        if (labelEl) {
          // Form field: build label + help + answer
          var labelText = strip(labelEl.innerHTML)
            .replace(/(\r\n|\n|\r)/gm, "")
            .replace(/[ ]+/g, " ");
          questionText = "### " + labelText;

          var helpEl = el.querySelector(".form__help");
          if (helpEl) {
            questionText += "\n\n" + strip(helpEl.innerHTML);
          }

          var wordLimit = el.dataset.wordLimit;
          if (wordLimit) {
            questionText += "\n\nLimit this field to " + wordLimit + " words.";
          }

          var listItems = el.querySelectorAll(".form__item > ul > li");
          var inputEl = el.querySelector("input");
          var richTextEl = el.querySelector(".tinymce4-editor");

          if (listItems.length) {
            var itemTexts = Array.from(listItems).map(function (li) {
              var text = strip(li.innerHTML);
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

  var applicationForm = document.querySelector(".application-form");
  if (!applicationForm) return;

  // Create the copy button
  var button = document.createElement("button");
  button.textContent = "Copy questions to clipboard";
  button.className = "btn sm:btn-sm w-full sm:w-auto js-clipboard-button";
  button.title =
    "Copies all the questions and user input to the clipboard in plain text.";
  button.type = "button";

  // Insert a copy above the form (styled to sit at the right)
  var topButton = button.cloneNode(true);
  topButton.style.display = "block";
  topButton.style.marginLeft = "auto";
  applicationForm.parentNode.insertBefore(topButton, applicationForm);

  // Insert a copy after the last button inside the form
  var lastButton = applicationForm.querySelector("button:last-of-type");
  if (lastButton) {
    lastButton.insertAdjacentElement("afterend", button);
  } else {
    applicationForm.appendChild(button);
  }

  // Attach click handler to all copy buttons
  document.querySelectorAll(".js-clipboard-button").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var text = getQuestions();

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          flashForm();
        });
      } else {
        // Fallback for older browsers
        var textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.className = "visually-hidden";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
        flashForm();
      }
    });
  });

  function flashForm() {
    applicationForm.classList.add("animate-flash");
    setTimeout(function () {
      applicationForm.classList.remove("animate-flash");
    }, 1200);
  }
})();
