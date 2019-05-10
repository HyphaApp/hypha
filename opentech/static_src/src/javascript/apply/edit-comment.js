(function ($) {

    'use strict';

    const comment = '.js-comment';
    const pageDown = '.js-pagedown';
    const feedMeta = '.js-feed-meta';
    const editBlock = '.js-edit-block';
    const lastEdited = '.js-last-edited';
    const editButton = '.js-edit-comment';
    const feedContent = '.js-feed-content';
    const cancelEditButton = '.js-cancel-edit';
    const submitEditButton = '.js-submit-edit';

    // handle edit
    $(editButton).click(function (e) {
        e.preventDefault();

        closeAllEditors();

        const editBlockWrapper = $(this).closest(feedContent).find(editBlock);
        const commentWrapper = $(this).closest(feedContent).find(comment);
        const commentContents = $(commentWrapper).attr('data-comment');

        // hide the edit link and original comment
        $(this).parent().hide();
        $(commentWrapper).hide();

        const markup = `
            <div class="js-pagedown form">
                <div id="wmd-button-bar-edit-comment" class="wmd-button-bar"></div>
                <textarea id="wmd-input-edit-comment" class="wmd-input" rows="10">${commentContents}</textarea>
                <div id="wmd-preview-edit-comment" class="wmd-preview"></div>
                <div class="wrapper--outer-space-medium">
                    <button class="button button--primary js-submit-edit" type="submit">Update</button>
                    <button class="button button--white js-cancel-edit">Cancel</button>
                </div>
            </div>
        `;

        // add the comment to the editor
        $(editBlockWrapper).append(markup);

        // run the editor
        initEditor();
    });

    // handle cancel
    $(document).on('click', cancelEditButton, function () {
        showComment(this);
        showEditButton(this);
        hidePageDownEditor(this);
    });

    // handle submit
    $(document).on('click', submitEditButton, function () {
        const commentContainer = $(this).closest(editBlock).siblings(comment);
        const id = $(commentContainer).attr('data-id');
        const editedComment = $(this).closest(pageDown).find('.wmd-preview').html();
        const commentMD = $(this).closest(editBlock).find('textarea').val();
        $(commentContainer).attr('data-comment', commentMD);

        // TODO - get correct URL
        const url = `${window.location.origin}/apply/api/comments/${id}/edit/`;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': $.cookie('csrftoken')
            },
            body: JSON.stringify({
                message: editedComment
            })
        }).then(response => response.json()).then(data => {
            updateComment(commentContainer, data.id, data.message);
            updateLastEdited(this, data.edited);
            showComment(this);
            showEditButton(this);
            hidePageDownEditor(this);
        });
    });

    const initEditor = () => {
        const converterOne = window.Markdown.getSanitizingConverter();
        const commentEditor = new window.Markdown.Editor(converterOne, '-edit-comment');
        commentEditor.run();
    };

    const showEditButton = (el) => {
        $(el).closest(editBlock).siblings(feedMeta).find(editButton).parent().show();
    };

    const hidePageDownEditor = (el) => {
        $(el).closest(pageDown).remove();
    };

    const showComment = (el) => {
        $(el).closest(editBlock).siblings(comment).show();
    };

    const updateLastEdited = (el, date) => {
        const parsedDate = new Date(date).toISOString().split('T')[0];
        const time = new Date(date).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});

        $(el).closest(feedContent).find(lastEdited).html(`${parsedDate} ${time}`);
    };

    const updateComment = (el, id, newComment) => {
        $(el).attr('data-id', id);
        $(el).html(newComment);
    };

    const closeAllEditors = () => {
        $(comment).show();
        $(pageDown).remove();
        $(editButton).parent().show();
    };

})(jQuery);
