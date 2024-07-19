import mistune


def markdown_to_html(text: str) -> str:
    """Converts markdown text to html.

    - No escape of HTML tags
    - With strikethrough plugin
    - With table plugin
    - With footnote plugin

    Args:
        text: markdown text

    Returns:
        Formatted markdown in HTML format
    """
    md = mistune.create_markdown(
        escape=False,
        hard_wrap=True,
        renderer="html",
        plugins=["strikethrough", "footnotes", "table", "url"],
    )

    return md(text)
