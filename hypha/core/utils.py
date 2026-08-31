import mistune
from django.conf import settings


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


def get_base_url() -> str:
    """Absolute base URL used to build links in outbound notifications.

    Returns the scheme, host and (if non-standard) port, without a trailing
    slash, e.g. "https://apply.example.org".

    Prefers the explicit `WAGTAILADMIN_BASE_URL` setting. Falls back to the
    default Wagtail site so installs that never configured it keep working.
    """
    # Imported here as this module is loaded before the app registry is ready.
    from wagtail.models import Site

    if base_url := getattr(settings, "WAGTAILADMIN_BASE_URL", None):
        return base_url.rstrip("/")

    if site := Site.objects.filter(is_default_site=True).first():
        return site.root_url

    return ""
