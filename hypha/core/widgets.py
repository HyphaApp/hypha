from django.forms.widgets import Media
from pagedown.widgets import PagedownWidget as PagedownWidgetBase


class PagedownWidget(PagedownWidgetBase):
    """
    Custom PagedownWidget to remove demo.css included in the default widget.
    """

    @property
    def media(self):
        return Media(css={"all": ("pagedown.css",)}, js=PagedownWidgetBase.Media.js)
