from datetime import date
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
from django.core.files.storage import default_storage
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Q
from django.db.models.expressions import RawSQL, OrderBy
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import Http404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.text import mark_safe, slugify
from django.utils.translation import ugettext_lazy as _

from django_fsm import can_proceed, FSMField, transition, RETURN_VALUE
from django_fsm.signals import post_transition
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

from wagtail.admin.utils import send_mail
from wagtail.core.fields import StreamField
from wagtail.core.models import Orderable
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormSubmission

from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.stream_forms.blocks import UploadableMediaBlock
from opentech.apply.stream_forms.models import AbstractStreamForm, BaseStreamForm
from opentech.apply.users.groups import REVIEWER_GROUP_NAME, STAFF_GROUP_NAME

from .admin_forms import WorkflowFormAdminForm
from .blocks import CustomFormFieldsBlock, MustIncludeFieldBlock, REQUIRED_BLOCK_NAMES
from .edit_handlers import FilteredFieldPanel, ReadOnlyPanel, ReadOnlyInlinePanel
from .workflow import (
    active_statuses,
    get_review_statuses,
    INITIAL_STATE,
    review_statuses,
    UserPermissions,
    WORKFLOWS,
    DETERMINATION_PHASES,
    DETERMINATION_RESPONSE_PHASES,
)

LIMIT_TO_STAFF = {'groups__name': STAFF_GROUP_NAME}
LIMIT_TO_REVIEWERS = {'groups__name': REVIEWER_GROUP_NAME}
LIMIT_TO_STAFF_AND_REVIEWERS = {'groups__name__in': [STAFF_GROUP_NAME, REVIEWER_GROUP_NAME]}


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
            MESSAGES.NEW_APPLICATION,
            request=request,
            user=form_submission.user,
            submission=form_submission,
        )
        return super().render_landing_page(request, form_submission=None, *args, **kwargs)

    content_panels = AbstractStreamForm.content_panels + [
        FieldPanel('workflow_name'),
        InlinePanel('forms', label="Forms"),
    ]


class EmailForm(AbstractEmailForm):
    """
    Defines the behaviour for pages that hold information about emailing applicants

    Email Confirmation Panel should be included to allow admins to make changes.
    """
    class Meta:
        abstract = True

    confirmation_text_extra = models.TextField(blank=True, help_text="Additional text for the application confirmation message.")

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        self.send_mail(submission)
        return submission

    def send_mail(self, submission):
        user = submission.user
        context = {
            'name': user.get_full_name(),
            'email': user.email,
            'project_name': submission.form_data.get('title'),
            'extra_text': self.confirmation_text_extra,
            'fund_type': self.title,
        }

        subject = self.subject if self.subject else 'Thank you for your submission to Open Technology Fund'
        send_mail(subject, render_to_string('funds/email/confirmation.txt', context), (user.email,), self.from_address, )

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


class FundType(EmailForm, WorkflowStreamForm):  # type: ignore
    class Meta:
        verbose_name = _("Fund")

    # Adds validation around forms & workflows. Isn't on Workflow class due to not displaying workflow field on Round
    base_form_class = WorkflowFormAdminForm

    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='fund_reviewers',
        limit_choices_to=LIMIT_TO_REVIEWERS,
        blank=True,
    )

    parent_page_types = ['apply_home.ApplyHomePage']
    subpage_types = ['funds.Round']

    def detail(self):
        # The location to find out more information
        return self.fund_public.first()

    @property
    def open_round(self):
        rounds = Round.objects.child_of(self).live().public().specific()
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


class FundForm(AbstractRelatedForm):
    fund = ParentalKey('FundType', related_name='forms')


class RoundForm(AbstractRelatedForm):
    round = ParentalKey('Round', related_name='forms')


class ApplicationForm(models.Model):
    name = models.CharField(max_length=255)
    form_fields = StreamField(CustomFormFieldsBlock())

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class Round(WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    parent_page_types = ['funds.FundType']
    subpage_types = []  # type: ignore

    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to=LIMIT_TO_STAFF,
        related_name='round_lead',
        on_delete=models.PROTECT,
    )
    reviewers = ParentalManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='rounds_reviewer',
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
                RoundForm.objects.create(round=self, form=new_form)

    def get_submit_meta_data(self, **kwargs):
        return super().get_submit_meta_data(
            page=self.get_parent(),
            round=self,
            **kwargs,
        )

    def process_form_submission(self, form):
        submission = super().process_form_submission(form)
        self.get_parent().specific.send_mail(submission)
        return submission

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


class LabType(EmailForm, WorkflowStreamForm, SubmittableStreamForm):  # type: ignore
    class Meta:
        verbose_name = _("Lab")

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


class JSONOrderable(models.QuerySet):
    json_field = ''

    def order_by(self, *field_names):
        if not self.json_field:
            raise ValueError(
                'json_field cannot be blank, please provide a field on which to perform the ordering'
            )

        def build_json_order_by(field):
            try:
                if field.replace('-', '') not in REQUIRED_BLOCK_NAMES:
                    return field
            except AttributeError:
                return field

            if field[0] == '-':
                descending = True
                field = field[1:]
            else:
                descending = False
            return OrderBy(RawSQL(f'LOWER({self.json_field}->>%s)', (field,)), descending=descending)

        field_ordering = [build_json_order_by(field) for field in field_names]
        return super().order_by(*field_ordering)


class ApplicationSubmissionQueryset(JSONOrderable):
    json_field = 'form_data'

    def active(self):
        return self.filter(status__in=active_statuses)

    def inactive(self):
        return self.exclude(status__in=active_statuses)

    def in_review(self):
        return self.filter(status__in=review_statuses)

    def in_review_for(self, user):
        user_review_statuses = get_review_statuses(user)
        return self.filter(status__in=user_review_statuses).filter(reviewers=user).exclude(reviews__author=user)

    def awaiting_determination_for(self, user):
        return self.filter(status__in=DETERMINATION_RESPONSE_PHASES).filter(lead=user)

    def current(self):
        # Applications which have the current stage active (have not been progressed)
        return self.exclude(next__isnull=False)


def make_permission_check(users):
    def can_transition(instance, user):
        if UserPermissions.STAFF in users and user.is_apply_staff:
            return True
        if UserPermissions.ADMIN in users and user.is_superuser:
            return True
        if UserPermissions.LEAD in users and instance.lead == user:
            return True
        if UserPermissions.APPLICANT in users and instance.user == user:
            return True
        return False

    return can_transition


def wrap_method(func):
    def wrapped(*args, **kwargs):
        # Provides a new function that can be wrapped with the django_fsm method
        # Without this using the same method for multiple transitions fails as
        # the fsm wrapping is overwritten
        return func(*args, **kwargs)
    return wrapped


def transition_id(target, phase):
    transition_prefix = 'transition'
    return '__'.join([transition_prefix, phase.stage.name.lower(), phase.name, target])


class AddTransitions(models.base.ModelBase):
    def __new__(cls, name, bases, attrs, **kwargs):
        for workflow in WORKFLOWS.values():
            for phase, data in workflow.items():
                for transition_name, action in data.transitions.items():
                    method_name = transition_id(transition_name, data)
                    permission_name = method_name + '_permission'
                    permission_func = make_permission_check(action['permissions'])

                    # Get the method defined on the parent or default to a NOOP
                    transition_state = wrap_method(attrs.get(action.get('method'), lambda *args, **kwargs: None))
                    # Provide a neat name for graph viz display
                    transition_state.__name__ = slugify(action['display'])

                    conditions = [attrs[condition] for condition in action.get('conditions', [])]
                    # Wrap with transition decorator
                    transition_func = transition(
                        attrs['status'],
                        source=phase,
                        target=transition_name,
                        permission=permission_func,
                        conditions=conditions,
                    )(transition_state)

                    # Attach to new class
                    attrs[method_name] = transition_func
                    attrs[permission_name] = permission_func

        def get_transition(self, transition):
            try:
                return getattr(self, transition_id(transition, self.phase))
            except TypeError:
                # Defined on the class
                return None
            except AttributeError:
                # For the other workflow
                return None

        attrs['get_transition'] = get_transition

        def get_actions_for_user(self, user):
            transitions = self.get_available_user_status_transitions(user)
            actions = [
                (transition.target, self.phase.transitions[transition.target]['display'])
                for transition in transitions if self.get_transition(transition.target)
            ]
            yield from actions

        attrs['get_actions_for_user'] = get_actions_for_user

        def perform_transition(self, action, user, request=None):
            transition = self.get_transition(action)
            if not transition:
                raise PermissionDenied(f'Invalid "{ action }" transition')
            if not can_proceed(transition):
                action = self.phase.transitions[action]
                raise PermissionDenied(f'You do not have permission to "{ action }"')

            transition(by=user, request=request)
            self.save()

        attrs['perform_transition'] = perform_transition

        return super().__new__(cls, name, bases, attrs, **kwargs)


class ApplicationSubmission(WorkflowHelpers, BaseStreamForm, AbstractFormSubmission, metaclass=AddTransitions):
    field_template = 'funds/includes/submission_field.html'

    form_data = JSONField(encoder=DjangoJSONEncoder)
    form_fields = StreamField(CustomFormFieldsBlock())
    page = models.ForeignKey('wagtailcore.Page', on_delete=models.PROTECT)
    round = models.ForeignKey('wagtailcore.Page', on_delete=models.PROTECT, related_name='submissions', null=True)
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        limit_choices_to=LIMIT_TO_STAFF,
        related_name='submission_lead',
        on_delete=models.PROTECT,
    )
    next = models.OneToOneField('self', on_delete=models.CASCADE, related_name='previous', null=True)
    reviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='submissions_reviewer',
        limit_choices_to=LIMIT_TO_STAFF_AND_REVIEWERS,
        blank=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    search_data = models.TextField()

    # Workflow inherited from WorkflowHelpers
    status = FSMField(default=INITIAL_STATE, protected=True)

    is_draft = False

    live_revision = models.OneToOneField(
        'ApplicationRevision',
        on_delete=models.CASCADE,
        related_name='live',
        null=True,
        editable=False,
    )
    draft_revision = models.OneToOneField(
        'ApplicationRevision',
        on_delete=models.CASCADE,
        related_name='draft',
        null=True,
        editable=False,
    )

    # Meta: used for migration purposes only
    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    objects = ApplicationSubmissionQueryset.as_manager()

    def not_progressed(self):
        return not self.next

    @transition(
        status, source='*',
        target=RETURN_VALUE(INITIAL_STATE, 'draft_proposal', 'invited_to_proposal'),
        permission=make_permission_check({UserPermissions.ADMIN}),
    )
    def restart_stage(self, **kwargs):
        """
        If running form the console please include your user using the kwarg "by"

        u = User.objects.get(email="<my@email.com>")
        for a in ApplicationSubmission.objects.all():
            a.restart_stage(by=u)
            a.save()
        """
        if hasattr(self, 'previous'):
            return 'draft_proposal'
        elif self.next:
            return 'invited_to_proposal'
        return INITIAL_STATE

    @property
    def stage(self):
        return self.phase.stage

    @property
    def phase(self):
        return self.workflow.get(self.status)

    @property
    def active(self):
        return self.status in active_statuses

    @property
    def last_edit(self):
        # Best estimate of last edit
        # TODO update when we have revisioning included
        return self.activities.first()

    def ensure_user_has_account(self):
        if self.user and self.user.is_authenticated:
            self.form_data['email'] = self.user.email
            self.form_data['full_name'] = self.user.get_full_name()
        else:
            # Rely on the form having the following must include fields (see blocks.py)
            email = self.form_data.get('email')
            full_name = self.form_data.get('full_name')

            User = get_user_model()
            if 'skip_account_creation_notification' in self.form_data:
                self.form_data.pop('skip_account_creation_notification', None)
                self.user, _ = User.objects.get_or_create(
                    email=email,
                    defaults={'full_name': full_name}
                )
            else:
                self.user, _ = User.objects.get_or_create_and_notify(
                    email=email,
                    site=self.page.get_site(),
                    defaults={'full_name': full_name}
                )

    def save_path(self, file_name):
        file_path = os.path.join('submissions', 'user', str(self.user.id), file_name)
        return default_storage.generate_filename(file_path)

    def handle_file(self, file):
        # File is potentially optional
        if file:
            try:
                filename = self.save_path(file.name)
            except AttributeError:
                # file is not changed, it is still the dictionary
                return file

            saved_name = default_storage.save(filename, file)
            return {
                'name': file.name,
                'path': saved_name,
                'url': default_storage.url(saved_name)
            }

    def handle_files(self, files):
        if isinstance(files, list):
            return [self.handle_file(file) for file in files]

        return self.handle_file(files)

    def get_from_parent(self, attribute):
        try:
            return getattr(self.round.specific, attribute)
        except AttributeError:
            # We are a lab submission
            return getattr(self.page.specific, attribute)

    def progress_application(self, **kwargs):
        submission_in_db = ApplicationSubmission.objects.get(id=self.id)

        self.id = None
        self.form_fields = self.get_from_parent('get_defined_fields')(self.stage)

        self.live_revision = None
        self.draft_revision = None
        self.save()

        submission_in_db.next = self
        submission_in_db.save()

    def new_data(self, data):
        self.is_draft = False
        self.form_data = data
        return self

    def from_draft(self):
        self.is_draft = True
        self.form_data = self.draft_revision.form_data
        return self

    def create_revision(self, draft=False, force=False, by=None, **kwargs):
        self.clean_submission()
        current_data = ApplicationSubmission.objects.get(id=self.id).form_data
        if current_data != self.form_data or force:
            if self.live_revision == self.draft_revision:
                revision = ApplicationRevision.objects.create(submission=self, form_data=self.form_data, author=by)
            else:
                revision = self.draft_revision
                revision.form_data = self.form_data
                revision.author = by
                revision.save()

            if draft:
                self.form_data = self.live_revision.form_data
            else:
                self.live_revision = revision

            self.draft_revision = revision
            self.save()

    def clean_submission(self):
        self.process_form_data()
        self.ensure_user_has_account()
        self.process_file_data()

    @property
    def must_include(self):
        return {
            field.block.name: field.id
            for field in self.form_fields
            if isinstance(field.block, MustIncludeFieldBlock)
        }

    def process_form_data(self):
        for field_name, field_id in self.must_include.items():
            response = self.form_data.pop(field_id, None)
            if response:
                self.form_data[field_name] = response

    def process_file_data(self):
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                file = self.form_data.get(field.id, {})
                self.form_data[field.id] = self.handle_files(file)

    def save(self, *args, **kwargs):
        if self.is_draft:
            raise ValueError('Cannot save with draft data')

        self.clean_submission()

        creating = not self.id
        if creating:
            # We are creating the object default to first stage
            self.workflow_name = self.get_from_parent('workflow_name')
            # Copy extra relevant information to the child
            self.lead = self.get_from_parent('lead')

        # add a denormed version of the answer for searching
        self.search_data = ' '.join(self.prepare_search_values())

        super().save(*args, **kwargs)

        if creating:
            self.reviewers.set(self.get_from_parent('reviewers').all())
            first_revision = ApplicationRevision.objects.create(submission=self, form_data=self.form_data)
            self.live_revision = first_revision
            self.draft_revision = first_revision
            self.save()

    @property
    def missing_reviewers(self):
        return self.reviewers.exclude(id__in=self.reviews.submitted().values('author'))

    @property
    def staff_not_reviewed(self):
        return self.missing_reviewers.staff()

    @property
    def reviewers_not_reviewed(self):
        return self.missing_reviewers.reviewers().exclude(id__in=self.staff_not_reviewed)

    def reviewed_by(self, user):
        return self.reviews.submitted().filter(author=user).exists()

    def has_permission_to_review(self, user):
        if user.is_apply_staff:
            return True

        if user in self.reviewers_not_reviewed:
            return True

        return False

    def can_review(self, user):
        if self.reviewed_by(user):
            return False

        return self.has_permission_to_review(user)

    def has_permission_to_add_determination(self, user):
        return user.is_superuser or self.lead == user

    @property
    def in_determination_phase(self):
        return self.status in DETERMINATION_PHASES

    @property
    def can_have_determination(self):
        if not self.in_determination_phase:
            return False

        try:
            return not self.determination.submitted
        except ObjectDoesNotExist:
            return True

    @property
    def raw_data(self):
        data = self.form_data.copy()
        for field_name, field_id in self.must_include.items():
            response = data.pop(field_name)
            data[field_id] = response
        return data

    def data_and_fields(self):
        for stream_value in self.form_fields:
            try:
                data = self.form_data[stream_value.id]
            except KeyError:
                pass  # It was a named field or a paragraph
            else:
                yield data, stream_value

    @property
    def fields(self):
        return [
            field.render(context={'data': data})
            for data, field in self.data_and_fields()
        ]

    def render_answers(self):
        return mark_safe(''.join(self.fields))

    def prepare_search_values(self):
        for data, stream in self.data_and_fields():
            value = stream.block.get_searchable_content(stream.value, data)
            if value:
                if isinstance(value, list):
                    yield ', '.join(value)
                else:
                    yield value

        # Add named fields into the search index
        for field in ['email', 'title']:
            yield getattr(self, field)

    def get_data(self):
        # Updated for JSONField
        form_data = self.form_data.copy()
        form_data.update({
            'submit_time': self.submit_time,
        })

        return form_data

    def get_absolute_url(self):
        return reverse('funds:submissions:detail', args=(self.id,))

    def __getattribute__(self, item):
        # __getattribute__ allows correct error handling from django compared to __getattr__
        # fall back to values defined on the data
        if item in REQUIRED_BLOCK_NAMES:
            return self.get_data()[item]
        return super().__getattribute__(item)

    def __str__(self):
        return f'{self.title} from {self.full_name} for {self.page.title}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.user}, {self.round}, {self.page}>'


@receiver(post_transition, sender=ApplicationSubmission)
def log_status_update(sender, **kwargs):
    instance = kwargs['instance']
    old_phase = instance.workflow[kwargs['source']]

    by = kwargs['method_kwargs']['by']
    request = kwargs['method_kwargs']['request']

    if request:
        messenger(
            MESSAGES.TRANSITION,
            user=by,
            request=request,
            submission=instance,
            old_phase=old_phase,
        )


class ApplicationRevision(models.Model):
    submission = models.ForeignKey(ApplicationSubmission, related_name='revisions', on_delete=models.CASCADE)
    form_data = JSONField(encoder=DjangoJSONEncoder)
    timestamp = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-timestamp']
