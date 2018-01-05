from django.db import models

from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

from opentech.utils.models import BasePage


class HomePage(BasePage):
    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']

    strapline = models.CharField(blank=True, max_length=255)
    call_to_action = models.ForeignKey('utils.CallToActionSnippet', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')

    search_fields = BasePage.search_fields + [
        index.SearchField('strapline'),
    ]

    content_panels = BasePage.content_panels + [
        FieldPanel('strapline'),
        SnippetChooserPanel('call_to_action'),
    ]
