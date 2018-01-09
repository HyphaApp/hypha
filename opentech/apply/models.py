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
from .forms import WorkflowFormAdminForm
from .workflow import SingleStage, DoubleStage


WORKFLOW_CLASS = {
    SingleStage.name: SingleStage,
    DoubleStage.name: DoubleStage,
}


class ApplyHomePage(Page, SocialFields, ListingFields):  # type: ignore
    # Only allow creating HomePages at the root level
    parent_page_types = ['wagtailcore.Page']
    subpage_types = ['FundType']

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


class FundType(AbstractStreamForm):
    parent_page_types = [ApplyHomePage]
    subpage_types = []  # type: ignore

    base_form_class = WorkflowFormAdminForm
    WORKFLOWS = {
        'single': SingleStage.name,
        'double': DoubleStage.name,
    }

    workflow = models.CharField(choices=WORKFLOWS.items(), max_length=100, default='single')

    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.forms.all()[0].fields

    @property
    def workflow_class(self):
        return WORKFLOW_CLASS[self.get_workflow_display()]

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow'),
        InlinePanel('forms', label="Forms"),
    ]


class FundForm(Orderable):
    form = models.ForeignKey('ApplicationForm')
    fund = ParentalKey('FundType', related_name='forms')

    @property
    def fields(self):
        return self.form.form_fields


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(CustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class Option(Orderable):
    value = models.CharField(max_length=255)
    category = ParentalKey('Category', related_name='options')


class Category(ClusterableModel):
    """Used to manage the global select questions used in most of the application form
    Also used in the front end by editors when writing about projects.

    When used in a form: name -> field label and help_text -> help_text
    """
    name = models.CharField(max_length=255)
    help_text = models.CharField(max_length=255, blank=True)

    @property
    def field_label(self):
        return self.name

    panels = [
        FieldPanel('name'),
        InlinePanel('options', label='Options'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
