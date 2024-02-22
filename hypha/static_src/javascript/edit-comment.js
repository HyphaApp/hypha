(function ($) {
    "use strict";

    const comment = ".js-comment";
    const pageDown = ".js-pagedown";
    const editBlock = ".js-edit-block";
    const editButton = ".js-edit-comment";
    const feedContent = ".js-feed-content";
    const commentError = ".js-comment-error";
    const cancelEditButton = ".js-cancel-edit";
    const submitEditButton = ".js-submit-edit";

    // handle edit
    $(editButton).click(function (e) {
        e.preventDefault();

        closeAllEditors();

        const editBlockWrapper = $(this).closest(feedContent).find(editBlock);
        const commentWrapper = $(this).closest(feedContent).find(comment);
        const commentContents = $(commentWrapper).attr("data-comment");

        // hide the edit link and original comment
        $(this).parent().hide();
        $(commentWrapper).hide();

        const markup = `
            <div class="js-pagedown form">
                <div id="wmd-button-bar-edit-comment" class="wmd-button-bar"></div>
                <textarea id="wmd-input-edit-comment" class="wmd-input" rows="10">${commentContents}</textarea>
                <div id="wmd-preview-edit-comment" class="wmd-preview"></div>
            </div>
        `;

        const buttons = `
                <div class="wrapper--outer-space-medium">
                    <button class="button button--primary js-submit-edit" type="submit">Update</button>
                    <button class="button button--white js-cancel-edit">Cancel</button>
                </div>
        `;

        // add the comment to the editor
        const markupEditor = $(markup).append(buttons);
        $(editBlockWrapper).append(markupEditor);

        // run the editor
        initEditor();
    });

    // handle cancel
    $(document).on("click", cancelEditButton, function () {
        showComment(this);
        showEditButton(this);
        hidePageDownEditor(this);
        if ($(commentError).length) {
            hideError();
        }
    });

    // handle submit
    $(document).on("click", submitEditButton, function () {
        const commentContainer = $(this).closest(editBlock).siblings(comment);
        const editedComment = $(this)
            .closest(pageDown)
            .find(".wmd-preview")
            .html();
        // const editedVisibility = $('input[name="radio-visibility"]:checked').val();
        const commentMD = $(this).closest(editBlock).find("textarea").val();
        const editUrl = $(commentContainer).attr("data-edit-url");

        fetch(editUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.Cookies.get("csrftoken"),
            },
            body: JSON.stringify({
                message: editedComment,
                // visibility: editedVisibility
            }),
        })
            .then((response) => {
                if (!response.ok) {
                    const error = Object.assign({}, response, {
                        status: response.status,
                        statusText: response.statusText,
                    });
                    return Promise.reject(error);
                }
                return response.json();
            })
            .then((data) => {
                updateComment(
                    commentContainer,
                    data.id,
                    data.message,
                    data.visibility,
                    data.edit_url,
                    commentMD
                );
                showComment(this);
                showEditButton(this);
                hidePageDownEditor(this);
            })
            .catch((error) => {
                if (error.status === 404) {
                    handleError(
                        this,
                        "Update unsuccessful. This comment has been edited elsewhere. To get the latest updates please refresh the page, but note any unsaved changes will be lost by doing so."
                    );
                } else {
                    handleError(
                        this,
                        "An error has occured. Please try again later."
                    );
                }
            });
    });

    const handleError = (el, message) => {
        $(el)
            .closest(editBlock)
            .append(
                `<p class="wrapper--error js-comment-error">${message}</p>`
            );
        $(el).attr("disabled", true);
    };

    const initEditor = () => {
        const converterOne = window.Markdown.getSanitizingConverter();
        const commentEditor = new window.Markdown.Editor(
            converterOne,
            "-edit-comment"
        );
        commentEditor.run();
    };

    const showEditButton = (el) => {
        $(editButton).parent().show();
    };

    const hidePageDownEditor = (el) => {
        $(el).closest(pageDown).remove();
    };

    const showComment = (el) => {
        $(el).closest(editBlock).siblings(comment).show();
    };

    const updateComment = (
        el,
        id,
        comment,
        visibility,
        editUrl,
        commentMarkdown
    ) => {
        $(el).html(comment);
        $(el).attr("data-id", id);
        $(el).attr("data-edit-url", editUrl);
        $(el).attr("data-comment", commentMarkdown);
        $(el).attr("data-visibility", visibility);
    };

    const closeAllEditors = () => {
        $(comment).show();
        $(pageDown).remove();
        $(editButton).parent().show();
    };

    const hideError = () => $(commentError).remove();
})(jQuery);
