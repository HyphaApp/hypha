from django import forms
from django.db import models

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    StreamFieldPanel,
)
from wagtail.wagtailcore.fields import StreamField
from wagtail.wagtailcore.models import Orderable

from opentech.apply.stream_forms.models import AbstractStreamForm

from .blocks import CustomFormFieldsBlock
from .forms import WorkflowFormAdminForm
from .workflow import SingleStage, DoubleStage


WORKFLOW_CLASS = {
    SingleStage.name: SingleStage,
    DoubleStage.name: DoubleStage,
}


class FundType(AbstractStreamForm):
    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = ['funds.Round']

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


class Round(AbstractStreamForm):
    parent_page_types = ['funds.FundType']
    subpage_types = []  # type: ignore


    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.get_parent().specific.forms.all()[0].fields
