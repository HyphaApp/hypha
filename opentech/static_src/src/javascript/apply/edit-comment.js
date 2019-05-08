(function ($) {

    'use strict';

    $('.js-edit-comment').click(function (e) {
        e.preventDefault();
        const editFormWrapper = $(this).closest('.js-feed-content').children('.js-edit-form');
        const commentWrapper = $(this).closest('.js-feed-content').children('.js-comment');
        const commentContents = $(this).closest('.js-feed-content').children('.js-comment').data('comment');

        // hide the edit link and original comment
        $(this).hide();
        $(commentWrapper).hide();

        const markup = `
            <div class="js-pagedown form">
                <div id="wmd-button-bar-edit-comment" class="wmd-button-bar"></div>
                <textarea id="wmd-input-edit-comment" class="wmd-input" rows="10">${commentContents}</textarea>
                <div id="wmd-preview-edit-comment" class="wmd-preview"></div>
                <div class="wrapper--top-outer-space-small">
                    <button class="button button--primary" type="submit">Update</button>
                    <button class="button button--white js-cancel-edit">Cancel</button>
                </div>
            </div>
        `;

        // add the comment to the editor
        $(editFormWrapper).append(markup);

        // run the editor
        const converterOne = Markdown.getSanitizingConverter();
        const commentEditor = new Markdown.Editor(converterOne, '-edit-comment');
        commentEditor.run();
    });

    $(document).on('click', '.js-cancel-edit', function () {
        // show the comment, edit button and remove the editor
        $(this).closest('.js-edit-form').prev('.js-comment').show();
        $(this).closest('.js-edit-form').siblings('.js-feed-meta').find('.js-edit-comment').show();
        $(this).closest('.js-pagedown').remove();
    });

})(jQuery);
