(function ($) {

    'use strict';

    // Strip html tags from text.
    function strip(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        return doc.body.textContent.trim() || '';
    }

    // Get all questions on the page/form.
    function get_questions() {
        var questions_text = [];
        questions_text.push('# ' + $('.header__title').html());
        $('.application-form').find('.form__group, .rich-text').each(function () {
            var question_text = '';
            var label_text = $(this).find('.form__question').html();
            if (label_text) {
                // Get the label, i.e. question.
                label_text = strip(label_text);
                label_text = label_text.replace(/(\r\n|\n|\r)/gm, '');
                label_text = label_text.replace(/[ ]+/g, ' ');
                question_text = '### ' + label_text;
            }
            else {
                // Get the sub headers and help text.
                question_text = strip($(this).html());
                if ($(this).find('h2')) {
                    question_text = '## ' + question_text;
                }
            }
            questions_text.push(question_text);
        });
        return questions_text.join('\n\n');
    }

    // Allow users to copy all questions to the clipboard.
    if (document.queryCommandSupported && document.queryCommandSupported('copy')) {
        var $button = $('<button/>')
            .text('Copy questions to clipboard')
            .addClass('link link--button link--button--narrow js-clipboard-button')
            .css({'display': 'block', 'margin-left': 'auto'})
            .attr('title', 'Copies all the questions to the clipboard in plain text.');
        $('.application-form').before($button);

        $('.js-clipboard-button').on('click', function (e) {
            e.preventDefault();
            var questions = get_questions();
            var $textarea = $('<textarea>').html(questions).addClass('visually-hidden');
            $textarea.appendTo('body');
            $textarea.select();
            document.execCommand('copy');
            $textarea.remove();
        });
    }

})(jQuery);
