(function ($) {
  /**
   * Strip html tags from text.
   * @param {string} html - The html
   * @returns {string} The text without html tags.
   */
  function strip(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    return doc.body.textContent.trim() || "";
  }

  /**
   * Get all questions on the page/form.
   * @returns {string} The questions and user input.
   */
  function get_questions() {
    var questions_text = [];
    var i = 1;
    questions_text.push("# " + $("h1:first").html());
    $(".application-form")
      .find(".form__group, .rich-text, h2, h3")
      .each(function () {
        var question_text = "";
        var label_text = $(this).find(".form__question").html();
        if (label_text) {
          // Get the label, i.e. question.
          label_text = strip(label_text);
          label_text = label_text.replace(/(\r\n|\n|\r)/gm, "");
          label_text = label_text.replace(/[ ]+/g, " ");
          question_text = "### " + label_text;

          var help_text = $(this).find(".form__help").html();
          var word_limit = $(this).attr("data-word-limit");
          var $input_list = $(this).find(".form__item > ul > li");
          var input_text = $(this).find("input").val();
          var rich_text = $(this).find(".tinymce4-editor").val();

          // Get help text.
          if (help_text) {
            question_text = question_text + "\n\n" + strip(help_text);
          }

          if (word_limit) {
            question_text =
              question_text +
              "\n\nLimit this field to " +
              word_limit +
              " words.";
          }

          // Get the user input if any.
          if ($input_list.length !== 0) {
            var input_list = [];
            var input_item = "";
            $input_list.each(function () {
              input_item = strip($(this).html());
              if ($(this).find("input").is(":checked")) {
                input_item = input_item + " (selected)";
              }
              input_list.push(input_item);
            });
            question_text = question_text + "\n\n" + input_list.join("\n");
          } else if (input_text) {
            question_text = question_text + "\n\n" + strip(input_text);
          } else if (rich_text) {
            question_text = question_text + "\n\n" + strip(rich_text);
          }
        } else {
          // Get the sub headers and help text.
          question_text = strip($(this).html());
          if ($(this).find("h2, h3")) {
            question_text = "## " + i + ". " + question_text;
            i++;
          }
        }
        questions_text.push(question_text);
      });
    return questions_text.join("\n\n");
  }

  // Allow users to copy all questions to the clipboard.
  if (
    document.queryCommandSupported &&
    document.queryCommandSupported("copy")
  ) {
    var $button = $("<button/>")
      .text("Copy questions to clipboard")
      .addClass("btn sm:btn-sm w-full sm:w-auto js-clipboard-button")
      .attr(
        "title",
        "Copies all the questions and user input to the clipboard in plain text."
      );
    var $application_form = $(".application-form");
    $button
      .clone()
      .css({ display: "block", "margin-left": "auto" })
      .insertBefore($application_form);
    $button.insertAfter($application_form.find("button").last());

    $(".js-clipboard-button").on("click", function (e) {
      e.preventDefault();
      $application_form.addClass("animate-flash");
      var questions = get_questions();
      var $textarea = $("<textarea>")
        .html(questions)
        .addClass("visually-hidden");
      $textarea.appendTo("body");
      $textarea.select();
      document.execCommand("copy");
      $textarea.remove();
      setTimeout(function () {
        $application_form.removeClass("animate-flash");
      }, 1200);
    });
  }
})(jQuery);
