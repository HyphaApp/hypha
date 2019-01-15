from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import OuterRef, Q, Subquery
from django.http import Http404
from django.utils.functional import cached_property
from django.utils.text import mark_safe
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalManyToManyField

from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.core.models import PageManager, PageQuerySet

from ..admin_forms import WorkflowFormAdminForm
from ..edit_handlers import ReadOnlyPanel, ReadOnlyInlinePanel

from .submissions import ApplicationSubmission
from .utils import admin_url, EmailForm, SubmittableStreamForm, WorkflowStreamForm, LIMIT_TO_REVIEWERS, LIMIT_TO_STAFF


class ApplicationBaseManager(PageQuerySet):
    def order_by_end_date(self):
        # OutRef path__startswith with find all descendants of the parent
        # We only have children, so no issues at this time
        rounds = RoundBase.objects.open().filter(path__startswith=OuterRef('path'))
        qs = self.public().live().annotate(end_date=Subquery(rounds.values('end_date')[:1]))
        return qs.order_by('end_date')


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

    slack_channel = models.TextField(blank=True, help_text=_('The slack #channel for notifications. Default channel is {slack_default}').format(slack_default=settings.SLACK_DESTINATION_ROOM))

    objects = PageManager.from_queryset(ApplicationBaseManager)()

    parent_page_types = ['apply_home.ApplyHomePage']

    def get_template(self, request, *args, **kwargs):
        # We want to force children to use our base template
        # template attribute is ignored by children
        return 'funds/application_base.html'

    def detail(self):
        # The location to find out more information
        return self.application_public.first()

    @cached_property
    def open_round(self):
        return RoundBase.objects.child_of(self).open().first()

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
        FieldPanel('slack_channel'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        EmailForm.email_tab,
        ObjectList(WorkflowStreamForm.promote_panels, heading='Promote'),
    ])


class RoundBaseManager(PageQuerySet):
    def open(self):
        rounds = self.live().public().specific()
        rounds = rounds.filter(
            Q(start_date__lte=date.today()) &
            Q(Q(end_date__isnull=True) | Q(end_date__gte=date.today()))
        )
        return rounds


class RoundBase(WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    is_creatable = False
    submission_class = ApplicationSubmission

    objects = PageManager.from_queryset(RoundBaseManager)()

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
        # Forms comes from parental key in models/forms.py
        ReadOnlyInlinePanel('forms', help_text="Copied from the fund."),
        ReadOnlyInlinePanel('review_forms', help_text="Copied from the fund."),
    ]

    edit_handler = TabbedInterface([
        ObjectList(content_panels, heading='Content'),
        ObjectList(SubmittableStreamForm.promote_panels, heading='Promote'),
    ])

    def get_template(self, request, *args, **kwargs):
        # Make sure all children use the shared template
        return 'funds/round.html'

    def get_landing_page_template(self, request, *args, **kwargs):
        # Make sure all children use the shared template
        return 'funds/round_landing.html'

    @cached_property
    def fund(self):
        return self.get_parent()

    @property
    def is_sealed(self):
        return self.sealed and self.is_open

    @property
    def is_open(self):
        return self.start_date <= date.today() <= self.end_date

    def save(self, *args, **kwargs):
        is_new = not self.id
        if is_new and hasattr(self, 'parent_page'):
            parent_page = self.parent_page[self.__class__][self.title]
            self.workflow_name = parent_page.workflow_name
            self.reviewers = parent_page.reviewers.all()

        super().save(*args, **kwargs)

        if is_new and hasattr(self, 'parent_page'):
            # Would be nice to do this using model clusters as part of the __init__
            self._copy_forms('forms')
            self._copy_forms('review_forms')

    def _copy_forms(self, field):
        for form in getattr(self.get_parent().specific, field).all():
            new_form = self._meta.get_field(field).related_model
            self._copy_form(form, new_form)

    def _copy_form(self, form, new_class):
        # Create a copy of the existing form object
        new_form = form.form
        new_form.id = None
        new_form.name = '{} for {} ({})'.format(new_form.name, self.title, self.get_parent().title)
        new_form.save()
        new_class.objects.create(round=self, form=new_form)

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

        if not self.id and hasattr(self, 'parent_page'):
            # Check if the create hook has added the parent page, we aren't an object yet.
            # Ensures we can access related objects during the clean phase instead of save.
            base_query = RoundBase.objects.child_of(self.parent_page[self.__class__][self.title])
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

    slack_channel = models.TextField(blank=True, help_text=_('The slack #channel for notifications. Default channel is {slack_default}').format(slack_default=settings.SLACK_DESTINATION_ROOM))

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = []  # type: ignore

    content_panels = WorkflowStreamForm.content_panels + [
        FieldPanel('lead'),
        FieldPanel('reviewers'),
        FieldPanel('slack_channel'),
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
