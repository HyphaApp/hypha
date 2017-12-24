from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Orderable, Page
from wagtail.wagtailsearch import index

from opentech.stream_forms.models import AbstractStreamForm
from opentech.utils.models import SocialFields, ListingFields

from .blocks import CustomFormFieldsBlock
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


class FundPage(AbstractStreamForm):
    parent_page_types = [ApplyHomePage]
    WORKFLOWS = (
        ('single', SingleStage.name),
        ('double', DoubleStage.name),
    )

    workflow = models.CharField(choices=WORKFLOWS, max_length=100, default=WORKFLOWS[0][0])
    form_fields = StreamField(CustomFormFieldsBlock())

    @property
    def workflow_class(self):
        return WORKFLOW_CLASS[self.get_workflow_display()]

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow'),
        StreamFieldPanel('form_fields'),
    ]


class Option(Orderable):
    value = models.CharField(max_length=255)
    category = ParentalKey('Category', related_name='options')


class Category(ClusterableModel):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
        InlinePanel('options', label='Options'),
    ]

    def __str__(self):
        return self.name
