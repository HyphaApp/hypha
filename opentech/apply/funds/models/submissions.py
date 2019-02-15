import os
from functools import partialmethod

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Count, IntegerField, OuterRef, Subquery, Sum, Q
from django.db.models.expressions import RawSQL, OrderBy
from django.db.models.functions import Coalesce
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify

from django_fsm import can_proceed, FSMField, transition, RETURN_VALUE
from django_fsm.signals import post_transition

from wagtail.core.fields import StreamField
from wagtail.contrib.forms.models import AbstractFormSubmission

from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.stream_forms.blocks import UploadableMediaBlock
from opentech.apply.stream_forms.files import StreamFieldDataEncoder
from opentech.apply.stream_forms.models import BaseStreamForm

from .mixins import AccessFormData
from .utils import LIMIT_TO_STAFF, LIMIT_TO_STAFF_AND_REVIEWERS, WorkflowHelpers
from ..blocks import ApplicationCustomFormFieldsBlock, NAMED_BLOCKS
from ..workflow import (
    active_statuses,
    DETERMINATION_RESPONSE_PHASES,
    get_review_statuses,
    INITIAL_STATE,
    PHASES,
    review_statuses,
    STAGE_CHANGE_ACTIONS,
    UserPermissions,
    WORKFLOWS,
)


class JSONOrderable(models.QuerySet):
    json_field = ''

    def order_by(self, *field_names):
        if not self.json_field:
            raise ValueError(
                'json_field cannot be blank, please provide a field on which to perform the ordering'
            )

        def build_json_order_by(field):
            try:
                if field.replace('-', '') not in NAMED_BLOCKS:
                    return field
            except AttributeError:
                return field

            if field[0] == '-':
                descending = True
                field = field[1:]
            else:
                descending = False
            db_table = self.model._meta.db_table
            return OrderBy(RawSQL(f'LOWER({db_table}.{self.json_field}->>%s)', (field,)), descending=descending, nulls_last=True)

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

    def in_review_for(self, user, assigned=True):
        user_review_statuses = get_review_statuses(user)
        qs = self.filter(Q(status__in=user_review_statuses), ~Q(reviews__author=user) | Q(reviews__is_draft=True))
        if assigned:
            qs = qs.filter(reviewers=user)
        return qs.distinct()

    def reviewed_by(self, user):
        return self.filter(reviews__author=user)

    def awaiting_determination_for(self, user):
        return self.filter(status__in=DETERMINATION_RESPONSE_PHASES).filter(lead=user)

    def current(self):
        # Applications which have the current stage active (have not been progressed)
        return self.exclude(next__isnull=False)

    def for_table(self, user):
        activities = self.model.activities.field.model
        latest_activity = activities.objects.filter(submission=OuterRef('id')).select_related('user')
        comments = activities.comments.filter(submission=OuterRef('id')).visible_to(user)

        reviews = self.model.reviews.field.model.objects.filter(submission=OuterRef('id'))

        return self.annotate(
            last_user_update=Subquery(latest_activity[:1].values('user__full_name')),
            last_update=Subquery(latest_activity.values('timestamp')[:1]),
            comment_count=Coalesce(
                Subquery(
                    comments.values('submission').order_by().annotate(count=Count('pk')).values('count'),
                    output_field=IntegerField(),
                ),
                0,
            ),
            review_count=Subquery(
                reviews.values('submission').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField(),
            ),
            review_staff_count=Subquery(
                reviews.by_staff().values('submission').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField(),
            ),
            review_submitted_count=Subquery(
                reviews.submitted().values('submission').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField(),
            ),
            review_recommendation=Subquery(
                reviews.submitted().values('submission').annotate(calc_recommendation=Sum('recommendation') / Count('recommendation')).values('calc_recommendation'),
                output_field=IntegerField(),
            ),
        ).prefetch_related(
            'reviews__author'
        ).select_related(
            'page',
            'round',
            'lead',
            'user',
            'previous__page',
            'previous__round',
        )


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

        def perform_transition(self, action, user, request=None, **kwargs):
            transition = self.get_transition(action)
            if not transition:
                raise PermissionDenied(f'Invalid "{ action }" transition')
            if not can_proceed(transition):
                action = self.phase.transitions[action]
                raise PermissionDenied(f'You do not have permission to "{ action }"')

            transition(by=user, request=request, **kwargs)
            self.save(update_fields=['status'])

            self.progress_stage_when_possible(user, request)

        attrs['perform_transition'] = perform_transition

        def progress_stage_when_possible(self, user, request):
            # Check to see if we can progress to a new stage from the current status
            for stage_transition in STAGE_CHANGE_ACTIONS:
                try:
                    self.perform_transition(stage_transition, user, request=request, notify=False)
                except PermissionDenied:
                    pass

        attrs['progress_stage_when_possible'] = progress_stage_when_possible

        return super().__new__(cls, name, bases, attrs, **kwargs)


class ApplicationSubmissionMetaclass(AddTransitions):
    def __new__(cls, name, bases, attrs, **kwargs):
        cls = super().__new__(cls, name, bases, attrs, **kwargs)

        # We want to access the redered display of the required fields.
        # Treat in similar way to django's get_FIELD_display
        for block_name in NAMED_BLOCKS:
            partial_method_name = f'_{block_name}_method'
            # We need to generate the partial method and the wrap it in property so
            # we can access the required fields like normal fields. e.g. self.title
            # Partial method requires __get__ to be called in order to bind it to the
            # class properly this is using the <name> -> _<name>_method -> _get_REQUIRED_value
            # call chain which instantiates each method correctly at the cost of an extra
            # lookup
            setattr(
                cls,
                partial_method_name,
                partialmethod(cls._get_REQUIRED_value, name=block_name),
            )
            setattr(
                cls,
                f'{block_name}',
                property(getattr(cls, partial_method_name)),
            )
            setattr(
                cls,
                f'get_{block_name}_display',
                partialmethod(cls._get_REQUIRED_display, name=block_name),
            )
        return cls


class ApplicationSubmission(
        WorkflowHelpers,
        BaseStreamForm,
        AccessFormData,
        AbstractFormSubmission,
        metaclass=ApplicationSubmissionMetaclass,
):
    field_template = 'funds/includes/submission_field.html'

    form_data = JSONField(encoder=StreamFieldDataEncoder)
    form_fields = StreamField(ApplicationCustomFormFieldsBlock())
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
        blank=True,
        through='AssignedReviewers',
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    search_data = models.TextField()

    # Workflow inherited from WorkflowHelpers
    status = FSMField(default=INITIAL_STATE, protected=True)

    screening_status = models.ForeignKey(
        'funds.ScreeningStatus',
        related_name='+',
        on_delete=models.SET_NULL,
        verbose_name='screening status',
        null=True,
    )

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

    def get_from_parent(self, attribute):
        try:

            return getattr(self.round.specific, attribute)
        except AttributeError:
            # We are a lab submission
            return getattr(self.page.specific, attribute)

    def progress_application(self, **kwargs):
        target = None
        for phase in STAGE_CHANGE_ACTIONS:
            transition = self.get_transition(phase)
            if can_proceed(transition):
                # We convert to dict as not concerned about transitions from the first phase
                # See note in workflow.py
                target = dict(PHASES)[phase].stage
        if not target:
            raise ValueError('Incorrect State for transition')

        submission_in_db = ApplicationSubmission.objects.get(id=self.id)

        self.id = None
        self.form_fields = self.get_from_parent('get_defined_fields')(target)

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
        self.form_data = self.deserialised_data(self.draft_revision.form_data, self.form_fields)
        return self

    def create_revision(self, draft=False, force=False, by=None, **kwargs):
        # Will return True/False if the revision was created or not
        self.clean_submission()
        current_submission = ApplicationSubmission.objects.get(id=self.id)
        current_data = current_submission.form_data
        if current_data != self.form_data or force:
            if self.live_revision == self.draft_revision:
                revision = ApplicationRevision.objects.create(submission=self, form_data=self.form_data, author=by)
            else:
                revision = self.draft_revision
                revision.form_data = self.form_data
                revision.author = by
                revision.save()

            if draft:
                self.form_data = current_submission.form_data
            else:
                self.live_revision = revision

            self.draft_revision = revision
            self.save()
            return revision
        return None

    def clean_submission(self):
        self.process_form_data()
        self.ensure_user_has_account()
        self.process_file_data(self.form_data)

    def process_form_data(self):
        for field_name, field_id in self.named_blocks.items():
            response = self.form_data.pop(field_id, None)
            if response:
                self.form_data[field_name] = response

    def extract_files(self):
        files = {}
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                files[field.id] = self.data(field.id) or []
                self.form_data.pop(field.id, None)
        return files

    def process_file_data(self, data):
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                file = self.process_file(data.get(field.id, []))
                folder = os.path.join('submission', str(self.id), field.id)
                try:
                    file.save(folder)
                except AttributeError:
                    for f in file:
                        f.save(folder)
                self.form_data[field.id] = file

    def save(self, *args, update_fields=list(), **kwargs):
        if update_fields and 'form_data' not in update_fields:
            # We don't want to use this approach if the user is sending data
            return super().save(*args, update_fields=update_fields, **kwargs)

        if self.is_draft:
            raise ValueError('Cannot save with draft data')

        creating = not self.id

        if creating:
            # We are creating the object default to first stage
            self.workflow_name = self.get_from_parent('workflow_name')
            # Copy extra relevant information to the child
            self.lead = self.get_from_parent('lead')

            # We need the submission id to correctly save the files
            files = self.extract_files()

        self.clean_submission()

        # add a denormed version of the answer for searching
        self.search_data = ' '.join(self.prepare_search_values())

        super().save(*args, **kwargs)

        if creating:
            self.process_file_data(files)
            for reviewer in self.get_from_parent('reviewers').all():
                AssignedReviewers.objects.create(
                    reviewer=reviewer,
                    submission=self
                )
            first_revision = ApplicationRevision.objects.create(
                submission=self,
                form_data=self.form_data,
                author=self.user,
            )
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

    def prepare_search_values(self):
        for field_id in self.question_field_ids:
            field = self.field(field_id)
            data = self.data(field_id)
            value = field.block.get_searchable_content(field.value, data)
            if value:
                if isinstance(value, list):
                    yield ', '.join(value)
                else:
                    yield value

        # Add named fields into the search index
        for field in ['full_name', 'email', 'title']:
            yield getattr(self, field)

    def get_absolute_url(self):
        return reverse('funds:submissions:detail', args=(self.id,))

    def __str__(self):
        return f'{self.title} from {self.full_name} for {self.page.title}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.user}, {self.round}, {self.page}>'

    # Methods for accessing data on the submission

    def get_data(self):
        # Updated for JSONField - Not used but base get_data will error
        form_data = self.form_data.copy()
        form_data.update({
            'submit_time': self.submit_time,
        })

        return form_data

    # Template methods for metaclass
    def _get_REQUIRED_display(self, name):
        return self.render_answer(name)

    def _get_REQUIRED_value(self, name):
        return self.form_data[name]


@receiver(post_transition, sender=ApplicationSubmission)
def log_status_update(sender, **kwargs):
    instance = kwargs['instance']
    old_phase = instance.workflow[kwargs['source']]

    by = kwargs['method_kwargs']['by']
    request = kwargs['method_kwargs']['request']
    notify = kwargs['method_kwargs'].get('notify', True)

    if request and notify:
        messenger(
            MESSAGES.TRANSITION,
            user=by,
            request=request,
            submission=instance,
            related=old_phase,
        )

        if instance.status in review_statuses:
            messenger(
                MESSAGES.READY_FOR_REVIEW,
                user=by,
                request=request,
                submission=instance,
            )

    if instance.status in STAGE_CHANGE_ACTIONS:
        messenger(
            MESSAGES.INVITED_TO_PROPOSAL,
            request=request,
            user=by,
            submission=instance,
        )


class ApplicationRevision(AccessFormData, models.Model):
    submission = models.ForeignKey(ApplicationSubmission, related_name='revisions', on_delete=models.CASCADE)
    form_data = JSONField(encoder=StreamFieldDataEncoder)
    timestamp = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'Revision for {self.submission.title} by {self.author} '

    @property
    def form_fields(self):
        return self.submission.form_fields

    def get_compare_url_to_latest(self):
        return reverse("funds:submissions:revisions:compare", kwargs={
            'submission_pk': self.submission.id,
            'to': self.submission.live_revision.id,
            'from': self.id,
        })

    def get_absolute_url(self):
        # Compares against the previous revision
        previous_revision = self.submission.revisions.filter(id__lt=self.id).first()
        return reverse("funds:submissions:revisions:compare", kwargs={
            'submission_pk': self.submission.id,
            'to': self.id,
            'from': previous_revision.id,
        })


class AssignedReviewersQuerySet(models.QuerySet):
    def with_roles(self):
        return self.filter(role__isnull=False)

    def without_roles(self):
        return self.filter(role__isnull=True)


class AssignedReviewers(models.Model):
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=LIMIT_TO_STAFF_AND_REVIEWERS,
    )
    submission = models.ForeignKey(
        ApplicationSubmission,
        related_name='assigned',
        on_delete=models.CASCADE
    )
    role = models.ForeignKey(
        'funds.ReviewerRole',
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
    )

    objects = AssignedReviewersQuerySet.as_manager()

    class Meta:
        unique_together = ('submission', 'role')

    def __str__(self):
        return f'{self.reviewer} as {self.role}'

    def __eq__(self, other):
        if not isinstance(other, models.Model):
            return False
        if self._meta.concrete_model != other._meta.concrete_model:
            return False
        my_pk = self.pk
        if my_pk is None:
            return self is other
        return all([
            self.reviewer_id == other.reviewer_id,
            self.role_id == other.role_id,
        ])
