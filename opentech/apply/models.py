from django.db import models
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailforms.models import AbstractForm
from wagtail.wagtailsearch import index

from opentech.stream_forms.blocks import FormFieldsBlock
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


class FundPage(AbstractForm):
    parent_page_types = [ApplyHomePage]
    WORKFLOWS = (
        ('single', SingleStage.name),
        ('double', DoubleStage.name),
    )

    workflow = models.CharField(choices=WORKFLOWS, max_length=100, default=WORKFLOWS[0][0])
    form_fields = StreamField(FormFieldsBlock())

    @property
    def workflow_class(self):
        return WORKFLOW_CLASS[self.get_workflow_display()]

    content_panels = AbstractForm.content_panels + [
        FieldPanel('workflow'),
        StreamFieldPanel('form_fields'),
    ]
