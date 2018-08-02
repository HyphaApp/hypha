from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.utils.text import mark_safe

from modelcluster.fields import ParentalManyToManyField

from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)

from ..admin_forms import WorkflowFormAdminForm
from ..edit_handlers import ReadOnlyPanel, ReadOnlyInlinePanel

from .submissions import ApplicationSubmission
from .forms import RoundBaseForm
from .utils import admin_url, EmailForm, SubmittableStreamForm, WorkflowStreamForm, LIMIT_TO_REVIEWERS, LIMIT_TO_STAFF


class ApplicationBase(EmailForm, WorkflowStreamForm):  # type: ignore
    is_createable = False

    # Adds validation around forms & workflows. Isn't on Workflow class due to not displaying workflow field on Round
    base_form_class = WorkflowFormAdminForm

    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_reviewers',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )

    parent_page_types = ['apply_home.ApplyHomePage']

    def detail(self):
        # The location to find out more information
        return self.fund_public.first()

    @property
    def open_round(self):
        rounds = RoundBase.objects.child_of(self).live().public().specific()
        return rounds.filter(
            Q(start_date__lte=date.today()) &
            Q(Q(end_date__isnull=True) | Q(end_date__gte=date.today()))
        ).first()

    def next_deadline(self):
        try:
            return self.open_round.end_date
        except AttributeError:
            # There isn't an open round
            return None

    def serve(self, request):
        if hasattr(request, 'is_preview') or not self.open_round:
            return super().serve(request)

        # delegate to the open_round to use the latest form instances
        request.show_round = True
        return self.open_round.serve(request)

    content_panels = WorkflowStreamForm.content_panels + [
        FieldPanel('reviewers'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading='Promote'),
    ])


class RoundBase(WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    is_creatable = False
    submission_class = ApplicationSubmission

    subpage_types = []  # type: ignore

    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to=LIMIT_TO_STAFF,
        related_name='%(class)s_lead',
        on_delete=models.PROTECT,
    )
    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='%(class)s_reviewer',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(
        blank=True,
        null=True,
        default=date.today,
        help_text='When no end date is provided the round will remain open indefinitely.'
    )
    sealed = models.BooleanField(default=False)

    content_panels = SubmittableStreamForm.content_panels + [
        FieldPanel('lead'),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('start_date'),
                FieldPanel('end_date'),
            ]),
        ], heading="Dates"),
        FieldPanel('reviewers'),
        ReadOnlyPanel('get_workflow_name_display', heading="Workflow"),
        ReadOnlyInlinePanel('forms', help_text="Are copied from the parent fund."),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(SubmittableStreamForm.promote_panels, heading='Promote'),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We attached the parent page as part of the before_create_hook
        if hasattr(self, 'parent_page'):
            self.workflow_name = self.parent_page.workflow_name
            self.reviewers = self.parent_page.reviewers.all()

    @property
    def is_sealed(self):
        return self.sealed and self.is_open

    @property
    def is_open(self):
        return self.start_date <= date.today() <= self.end_date

    def save(self, *args, **kwargs):
        is_new = not self.id
        if is_new and hasattr(self, 'parent_page'):
            # Ensure that the workflow hasn't changed
            self.workflow_name = self.parent_page.workflow_name

        super().save(*args, **kwargs)

        if is_new and hasattr(self, 'parent_page'):
            # Would be nice to do this using model clusters as part of the __init__
            for form in self.parent_page.forms.all():
                # Create a copy of the existing form object
                new_form = form.form
                new_form.id = None
                new_form.name = '{} for {} ({})'.format(new_form.name, self.title, self.get_parent().title)
                new_form.save()
                RoundBaseForm.objects.create(round=self, form=new_form)

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self.get_parent(),
            round=self,
            **kwargs,
        )

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

        if hasattr(self, 'parent_page'):
            # Check if the create hook has added the parent page, we aren't an object yet.
            # Ensures we can access related objects during the clean phase instead of save.
            base_query = RoundBase.objects.child_of(self.parent_page)
        else:
            # don't need parent page, we are an actual object now.
            base_query = RoundBase.objects.sibling_of(self)

        conflicting_rounds = base_query.filter(
            conflict_query
        ).exclude(id=self.id)

        if conflicting_rounds.exists():
            error_message = mark_safe('Overlaps with the following rounds:<br> {}'.format(
                '<br>'.join([
                    f'<a href="{admin_url(round)}">{round.title}</a>: {round.start_date} - {round.end_date}'
                    for round in conflicting_rounds]
                )
            ))
            error = {
                'start_date': error_message,
            }
            if self.end_date:
                error['end_date'] = error_message

            raise ValidationError(error)

    def serve(self, request):
        if hasattr(request, 'is_preview') or hasattr(request, 'show_round'):
            return super().serve(request)

        # We hide the round as only the open round is used which is displayed through the
        # fund page
        raise Http404()


class LabBase(EmailForm, WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    is_createable = False
    submission_class = ApplicationSubmission

    # Adds validation around forms & workflows.
    base_form_class = WorkflowFormAdminForm

    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to=LIMIT_TO_STAFF,
        related_name='lab_lead',
        on_delete=models.PROTECT,
    )
    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='labs_reviewer',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = []  # type: ignore

    content_panels = WorkflowStreamForm.content_panels + [
        FieldPanel('lead'),
        FieldPanel('reviewers'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading='Promote'),
    ])

    def detail(self):
        # The location to find out more information
        return self.lab_public.first()

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self,
            round=None,
            **kwargs,
        )

    def open_round(self):
        return self.live
