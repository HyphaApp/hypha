from datetime import date

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.utils.text import mark_safe

from modelcluster.fields import ParentalKey
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    FieldRowPanel,
    MultiFieldPanel,
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

    @property
    def open_round(self):
        rounds = Round.objects.child_of(self).live().public().specific()
        return rounds.filter(
            Q(start_date__lte=date.today()) &
            Q(Q(end_date__isnull=True) | Q(end_date__gte=date.today()))
        ).first()

    def next_deadline(self):
        return self.open_round.end_date

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow'),
        InlinePanel('forms', label="Forms"),
    ]

    def serve(self, request):
        if hasattr(request, 'is_preview'):
            return super().serve(request)

        # delegate to the open_round to use the latest form instances
        request.show_page = True
        return self.open_round.serve(request)


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

    start_date = models.DateField(default=date.today)
    end_date = models.DateField(
        blank=True,
        null=True,
        default=date.today,
        help_text='If no end date is provided the round will remain open.'
    )

    content_panels = AbstractStreamForm.content_panels + [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('start_date'),
                FieldPanel('end_date'),
            ]),
        ], heading="Dates")
    ]

    def get_defined_fields(self):
        # Only return the first form, will need updating for when working with 2 stage WF
        return self.get_parent().specific.forms.all()[0].fields

    def clean(self):
        super().clean()

        if self.end_date and self.start_date > self.end_date:
            raise ValidationError({
                'end_date': 'End date must come after the start date',
            })

        if self.end_date:
            conflict_query = (
                Q(start_date__range=[self.start_date, self.end_date]) |
                Q(end_date__range=[self.start_date, self.end_date]) |
                Q(start_date__lte=self.start_date, end_date__gte=self.end_date)
            )
        else:
            conflict_query = (
                Q(start_date__lte=self.start_date, end_date__isnull=True) |
                Q(end_date__gte=self.start_date)
            )

        conflicting_rounds = Round.objects.sibling_of(self).filter(
            conflict_query
        ).exclude(id=self.id)

        if conflicting_rounds.exists():
            error_message = mark_safe('Overlaps with the following rounds:<br> {}'.format(
                '<br>'.join([f'{round.start_date} - {round.end_date}' for round in conflicting_rounds])
            ))
            error = {
                'start_date': error_message,
            }
            if self.end_date:
                error['end_date'] = error_message

            raise ValidationError(error)

    def serve(self, request):
        if hasattr(request, 'is_preview') or hasattr(request, 'show_page'):
            return super().serve(request)

        # We hide the round as only the open round is used which is displayed through the
        # fund page
        raise Http404()
