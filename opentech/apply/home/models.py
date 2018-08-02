from wagtail.admin.edit_handlers import FieldPanel
from wagtail.core.models import Page
from wagtail.search import index

from django.db import models


class ApplyHomePage(Page):
    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']
    subpage_types = ['funds.FundType', 'funds.LabType', 'funds.RequestForPartners']

    strapline = models.CharField(blank=True, max_length=255)

    search_fields = Page.search_fields + [
        index.SearchField('strapline'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('strapline'),
    ]
