from django.db import models
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from wagtail.wagtailcore.models import Page
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.edit_handlers import SnippetChooserPanel

from opentech.utils.models import SocialFields, ListingFields

from .workflow import SingleStage, DoubleStage


WORKFLOW_CLASS = {
    SingleStage.name: SingleStage,
    DoubleStage.name: DoubleStage,
}

class ApplyHomePage(Page, SocialFields, ListingFields):
    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']

    strapline = models.CharField(blank=True, max_length=255)

    search_fields = Page.search_fields + [
        index.SearchField('strapline'),
    ]

    content_panels = Page.content_panels + [
        FieldPanel('strapline'),
    ]

    promote_panels = (
        Page.promote_panels +
        SocialFields.promote_panels +
        ListingFields.promote_panels
    )


class FundPage(Page):
    parent_page_types = [ApplyHomePage]
    WORKFLOWS = (
        ('single', SingleStage.name),
        ('double', DoubleStage.name),
    )

    workflow = models.CharField(choices=WORKFLOWS, max_length=100, default=WORKFLOWS[0][0])

    @property
    def workflow_class(self):
        return WORKFLOW_CLASS[self.get_workflow_display()]
