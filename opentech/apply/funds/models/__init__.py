from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from django.utils.text import mark_safe
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey, ParentalManyToManyField

from wagtail.admin.edit_handlers import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    StreamFieldPanel,
    TabbedInterface,
)
from wagtail.core.fields import StreamField
from wagtail.core.models import Orderable
from wagtail.contrib.forms.models import AbstractEmailForm

from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.stream_forms.models import AbstractStreamForm
from opentech.apply.users.groups import REVIEWER_GROUP_NAME, STAFF_GROUP_NAME

from ..admin_forms import WorkflowFormAdminForm
from ..blocks import ApplicationCustomFormFieldsBlock
from ..edit_handlers import FilteredFieldPanel, ReadOnlyPanel, ReadOnlyInlinePanel
from ..workflow import WORKFLOWS

LIMIT_TO_STAFF = {'groups__name': STAFF_GROUP_NAME}
LIMIT_TO_REVIEWERS = {'groups__name': REVIEWER_GROUP_NAME}
LIMIT_TO_STAFF_AND_REVIEWERS = {'groups__name__in': [STAFF_GROUP_NAME, REVIEWER_GROUP_NAME]}


class WorkflowHelpers(models.Model):
    """
    Defines the common methods and fields for working with Workflows within Django models
    """
    class Meta:
        abstract = True

    WORKFLOW_CHOICES = {
        name: workflow.name
        for name, workflow in WORKFLOWS.items()
    }

    workflow_name = models.CharField(choices=WORKFLOW_CHOICES.items(), max_length=100, default='single', verbose_name="Workflow")

    @property
    def workflow(self):
        return WORKFLOWS[self.workflow_name]


from .submissions import ApplicationSubmission, ApplicationRevision


__all__ = ['ApplicationSubmission', 'ApplicationRevision']


def admin_url(page):
    return reverse('wagtailadmin_pages:edit', args=(page.id,))


class SubmittableStreamForm(AbstractStreamForm):
    """
    Controls how stream forms are submitted. Any Page allowing submissions should inherit from here.
    """
    class Meta:
        abstract = True

    def get_submission_class(self):
        return ApplicationSubmission

    def process_form_submission(self, form):
        if not form.user.is_authenticated:
            form.user = None
        return self.get_submission_class().objects.create(
            form_data=form.cleaned_data,
            form_fields=self.get_defined_fields(),
            **self.get_submit_meta_data(user=form.user),
        )

    def get_submit_meta_data(self, **kwargs):
        return kwargs


class WorkflowStreamForm(WorkflowHelpers, AbstractStreamForm):  # type: ignore
    """
    Defines the common methods and fields for working with Workflows within Wagtail pages
    """
    class Meta:
        abstract = True

    def get_defined_fields(self, stage=None):
        if not stage:
            form_index = 0
        else:
            form_index = self.workflow.stages.index(stage)
        return self.forms.all()[form_index].fields

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        # We only reach this page after creation of a new submission
        # Hook in to notify about new applications
        messenger(
            MESSAGES.NEW_SUBMISSION,
            request=request,
            user=form_submission.user,
            submission=form_submission,
        )
        return super().render_landing_page(request, form_submission=None, *args, **kwargs)

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow_name'),
        InlinePanel('forms', label="Forms"),
        InlinePanel('review_forms', label="Review Forms")
    ]


class EmailForm(AbstractEmailForm):
    """
    Defines the behaviour for pages that hold information about emailing applicants

    Email Confirmation Panel should be included to allow admins to make changes.
    """
    class Meta:
        abstract = True

    confirmation_text_extra = models.TextField(blank=True, help_text="Additional text for the application confirmation message.")

    def send_mail(self, submission):
        # Make sure we don't send emails to users here. Messaging handles that
        pass

    email_confirmation_panels = [
        MultiFieldPanel(
            [
                FieldRowPanel([
                    FieldPanel('from_address', classname="col6"),
                    FieldPanel('to_address', classname="col6"),
                ]),
                FieldPanel('subject'),
                FieldPanel('confirmation_text_extra'),
            ],
            heading="Confirmation email",
        )
    ]

    email_tab = ObjectList(email_confirmation_panels, heading='Confirmation email')


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

    def _open_for(self, round_type):
        rounds = round_type.objects.child_of(self).live().public().specific()
        return rounds.filter(
            Q(start_date__lte=date.today()) &
            Q(Q(end_date__isnull=True) | Q(end_date__gte=date.today()))
        ).first()

    @property
    def open_round(self):
        open_round = self._open_for(Round)
        open_sealed_round = self._open_for(SealedRound)
        return open_round or open_sealed_round

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


class FundType(ApplicationBase):
    subpage_types = ['funds.Round']

    class Meta:
        verbose_name = _("Fund")


class RequestForPartners(ApplicationBase):
    subpage_types = ['funds.Round', 'funds.SealedRound']

    class Meta:
        verbose_name = _("RFP")


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(ApplicationCustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class AbstractRelatedForm(Orderable):
    form = models.ForeignKey('ApplicationForm', on_delete=models.PROTECT)

    panels = [
        FilteredFieldPanel('form', filter_query={'roundform__isnull': True})
    ]

    @property
    def fields(self):
        return self.form.form_fields

    class Meta(Orderable.Meta):
        abstract = True

    def __eq__(self, other):
        try:
            return self.fields == other.fields
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class ApplicationBaseForm(AbstractRelatedForm):
    application = ParentalKey('ApplicationBase', related_name='forms')


class RoundBaseForm(AbstractRelatedForm):
    round = ParentalKey('RoundBase', related_name='forms')


class AbstractRelatedReviewForm(Orderable):
    form = models.ForeignKey('review.ReviewForm', on_delete=models.PROTECT)

    panels = [
        FieldPanel('form')
    ]

    @property
    def fields(self):
        return self.form.form_fields

    class Meta(Orderable.Meta):
        abstract = True

    def __eq__(self, other):
        try:
            return self.fields == other.fields
        except AttributeError:
            return False

    def __str__(self):
        return self.form.name


class ApplicationBaseReviewForm(AbstractRelatedReviewForm):
    fund = ParentalKey('ApplicationBase', related_name='review_forms')


class RoundBase(WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    is_creatable = False

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
            base_query = Round.objects.child_of(self.parent_page)
        else:
            # don't need parent page, we are an actual object now.
            base_query = Round.objects.sibling_of(self)

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


class Round(RoundBase):
    parent_page_types = ['funds.FundType', 'funds.RequestForPartners']


class SealedRound(RoundBase):
    parent_page_types = ['funds.RequestForPartners']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sealed = True


class LabType(EmailForm, WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    class Meta:
        verbose_name = _("Lab")

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


class LabForm(AbstractRelatedForm):
    lab = ParentalKey('LabType', related_name='forms')


class LabReviewForm(AbstractRelatedReviewForm):
    lab = ParentalKey('LabType', related_name='review_forms')
