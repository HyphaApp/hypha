import json
from functools import partialmethod

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import (
    Avg,
    Case,
    Count,
    F,
    FloatField,
    IntegerField,
    OuterRef,
    Prefetch,
    Q,
    Subquery,
    Sum,
    When,
)
from django.db.models.expressions import OrderBy, RawSQL
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast, Coalesce
from django.dispatch import receiver
from django.urls import reverse
from django.utils.text import slugify
from django_fsm import RETURN_VALUE, FSMField, can_proceed, transition
from django_fsm.signals import post_transition
from wagtail.contrib.forms.models import AbstractFormSubmission
from wagtail.core.fields import StreamField

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.categories.models import MetaTerm
from hypha.apply.determinations.models import Determination
from hypha.apply.flags.models import Flag
from hypha.apply.review.models import ReviewOpinion
from hypha.apply.review.options import AGREE, DISAGREE, MAYBE
from hypha.apply.stream_forms.files import StreamFieldDataEncoder
from hypha.apply.stream_forms.models import BaseStreamForm

from ..blocks import NAMED_BLOCKS, ApplicationCustomFormFieldsBlock
from ..workflow import (
    COMMUNITY_REVIEW_PHASES,
    DETERMINATION_RESPONSE_PHASES,
    DRAFT_STATE,
    INITIAL_STATE,
    PHASES,
    PHASES_MAPPING,
    STAGE_CHANGE_ACTIONS,
    WORKFLOWS,
    UserPermissions,
    accepted_statuses,
    active_statuses,
    dismissed_statuses,
    ext_or_higher_statuses,
    get_review_active_statuses,
    review_statuses,
)
from .mixins import AccessFormData
from .reviewer_role import ReviewerRole
from .utils import (
    COMMUNITY_REVIEWER_GROUP_NAME,
    LIMIT_TO_PARTNERS,
    LIMIT_TO_REVIEWER_GROUPS,
    LIMIT_TO_STAFF,
    REVIEW_GROUPS,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
    WorkflowHelpers,
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

    def in_community_review(self, user):
        qs = self.filter(Q(status__in=COMMUNITY_REVIEW_PHASES), ~Q(user=user), ~Q(reviews__author=user) | Q(reviews__is_draft=True))
        qs = qs.exclude(reviews__opinions__opinion=AGREE, reviews__opinions__author=user)
        return qs.distinct()

    def in_review(self):
        return self.filter(status__in=review_statuses)

    def in_review_for(self, user, assigned=True):
        user_review_statuses = get_review_active_statuses(user)
        qs = self.prefetch_related('reviews__author__reviewer')
        qs = qs.filter(Q(status__in=user_review_statuses), ~Q(reviews__author__reviewer=user) | Q(reviews__is_draft=True))
        if assigned:
            qs = qs.filter(reviewers=user)
            # If this user has agreed with a review, then they have reviewed this submission already
            qs = qs.exclude(reviews__opinions__opinion=AGREE, reviews__opinions__author__reviewer=user)
        return qs.distinct()

    def for_reviewer_settings(self, user, reviewer_settings):
        qs = self
        if reviewer_settings.submission == 'reviewed':
            qs = qs.reviewed_by(user)
        if reviewer_settings.state == 'ext_state_or_higher':
            qs = qs.filter(status__in=ext_or_higher_statuses)
        if reviewer_settings.outcome == 'accepted':
            qs = qs.filter(status__in=accepted_statuses)
        if reviewer_settings.outcome == 'all_except_dismissed':
            qs = qs.exclude(status__in=dismissed_statuses)
        if reviewer_settings.assigned:
            qs = qs.filter(reviewers=user)
        return qs.distinct()

    def reviewed_by(self, user):
        return self.filter(reviews__author__reviewer=user)

    def flagged_by(self, user):
        return self.filter(flags__user=user, flags__type=Flag.USER)

    def flagged_staff(self):
        return self.filter(flags__type=Flag.STAFF)

    def partner_for(self, user):
        return self.filter(partners=user)

    def awaiting_determination_for(self, user):
        return self.filter(status__in=DETERMINATION_RESPONSE_PHASES).filter(lead=user)

    def undetermined(self):
        determined_submissions = Determination.objects.filter(submission__in=self).final().values('submission')
        return self.exclude(pk__in=determined_submissions)

    def current(self):
        # Applications which have the current stage active (have not been progressed)
        return self.exclude(next__isnull=False)

    def current_accepted(self):
        # Applications which have the current stage active (have not been progressed)
        return self.filter(status__in=PHASES_MAPPING['accepted']['statuses']).current()

    def value(self):
        return self.annotate(
            value=Cast(KeyTextTransform('value', 'form_data'), output_field=FloatField())
        ).aggregate(
            Count('value'),
            Avg('value'),
            Sum('value'),
        )

    def exclude_draft(self):
        return self.exclude(status=DRAFT_STATE)

    def with_latest_update(self):
        activities = self.model.activities.rel.model
        latest_activity = activities.objects.filter(submission=OuterRef('id')).select_related('user')
        return self.annotate(
            last_user_update=Subquery(latest_activity[:1].values('user__full_name')),
            last_update=Subquery(latest_activity.values('timestamp')[:1]),
        )

    def for_table(self, user):
        activities = self.model.activities.rel.model
        comments = activities.comments.filter(submission=OuterRef('id')).visible_to(user)
        roles_for_review = self.model.assigned.field.model.objects.with_roles().filter(
            submission=OuterRef('id'), reviewer=user)

        review_model = self.model.reviews.field.model
        reviews = review_model.objects.filter(submission=OuterRef('id'))
        opinions = review_model.opinions.field.model.objects.filter(review__submission=OuterRef('id'))
        reviewers = self.model.assigned.field.model.objects.filter(submission=OuterRef('id'))

        return self.with_latest_update().annotate(
            comment_count=Coalesce(
                Subquery(
                    comments.values('submission').order_by().annotate(count=Count('pk')).values('count'),
                    output_field=IntegerField(),
                ),
                0,
            ),
            opinion_disagree=Subquery(
                opinions.filter(opinion=DISAGREE).values(
                    'review__submission'
                ).annotate(count=Count('*')).values('count')[:1],
                output_field=IntegerField(),
            ),
            review_staff_count=Subquery(
                reviewers.staff().values('submission').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField(),
            ),
            review_count=Subquery(
                reviewers.values('submission').annotate(count=Count('pk')).values('count'),
                output_field=IntegerField(),
            ),
            review_submitted_count=Subquery(
                reviewers.reviewed().values('submission').annotate(
                    count=Count('pk', distinct=True)
                ).values('count'),
                output_field=IntegerField(),
            ),
            review_recommendation=Case(
                When(opinion_disagree__gt=0, then=MAYBE),
                default=Subquery(
                    reviews.submitted().values('submission').annotate(
                        calc_recommendation=Sum('recommendation') / Count('recommendation'),
                    ).values('calc_recommendation'),
                    output_field=IntegerField(),
                )
            ),
            role_icon=Subquery(roles_for_review[:1].values('role__icon')),
        ).prefetch_related(
            Prefetch(
                'assigned',
                queryset=AssignedReviewers.objects.reviewed().review_order().select_related(
                    'reviewer',
                ).prefetch_related(
                    Prefetch('review__opinions', queryset=ReviewOpinion.objects.select_related('author')),
                ),
                to_attr='has_reviewed'
            ),
            Prefetch(
                'assigned',
                queryset=AssignedReviewers.objects.not_reviewed().staff(),
                to_attr='hasnt_reviewed'
            )
        ).select_related(
            'page',
            'round',
            'lead',
            'user',
            'previous__page',
            'previous__round',
            'previous__lead',
        ).prefetch_related(
            'screening_statuses'
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

            self.progress_stage_when_possible(user, request, **kwargs)

        attrs['perform_transition'] = perform_transition

        def progress_stage_when_possible(self, user, request, notify=None, **kwargs):
            # Check to see if we can progress to a new stage from the current status
            for stage_transition in STAGE_CHANGE_ACTIONS:
                try:
                    self.perform_transition(stage_transition, user, request=request, notify=False, **kwargs)
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
    form_data = models.JSONField(encoder=StreamFieldDataEncoder)
    form_fields = StreamField(ApplicationCustomFormFieldsBlock())
    summary = models.TextField(default='', null=True, blank=True)
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
    partners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='submissions_partner',
        limit_choices_to=LIMIT_TO_PARTNERS,
        blank=True,
    )
    meta_terms = models.ManyToManyField(
        MetaTerm,
        related_name='submissions',
        blank=True,
    )
    flags = GenericRelation(
        Flag,
        content_type_field='target_content_type',
        object_id_field='target_object_id',
        related_query_name='submission',
    )
    activities = GenericRelation(
        'activity.Activity',
        content_type_field='source_content_type',
        object_id_field='source_object_id',
        related_query_name='submission',
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    search_data = models.TextField()

    # Workflow inherited from WorkflowHelpers
    status = FSMField(default=INITIAL_STATE, protected=True)

    screening_statuses = models.ManyToManyField(
        'funds.ScreeningStatus',
        related_name='submissions',
        blank=True
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

    @property
    def is_determination_form_attached(self):
        """
        We use old django determination forms but now as we are moving
        to streamfield determination forms which can be created and attached
        to funds in admin.

        This method checks if there are new determination forms attached to the
        submission or we would still use the old determination forms for backward
        compatibility.
        """
        return self.get_from_parent('determination_forms').count() > 0

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
        prev_meta_terms = submission_in_db.meta_terms.all()

        self.id = None
        proposal_form = kwargs.get('proposal_form')
        proposal_form = int(proposal_form) if proposal_form else 0
        self.form_fields = self.get_from_parent('get_defined_fields')(target, form_index=proposal_form)

        self.live_revision = None
        self.draft_revision = None
        self.save()
        self.meta_terms.set(prev_meta_terms)

        submission_in_db.next = self
        submission_in_db.save()

    def new_data(self, data):
        self.is_draft = False
        self.form_data = data
        return self

    def from_draft(self):
        self.is_draft = True
        self.form_data = self.deserialised_data(self, self.draft_revision.form_data, self.form_fields)
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
                self.search_data = ' '.join(self.prepare_search_values())

            self.draft_revision = revision
            self.save(skip_custom=True)
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

    def save(self, *args, update_fields=list(), skip_custom=False, **kwargs):
        if update_fields and 'form_data' not in update_fields:
            # We don't want to use this approach if the user is sending data
            return super().save(*args, update_fields=update_fields, **kwargs)
        elif skip_custom:
            return super().save(*args, **kwargs)

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
                AssignedReviewers.objects.get_or_create_for_user(
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
    def has_all_reviewer_roles_assigned(self):
        return self.assigned.with_roles().count() == ReviewerRole.objects.count()

    @property
    def community_review(self):
        return self.status in COMMUNITY_REVIEW_PHASES

    @property
    def missing_reviewers(self):
        reviewers_submitted = self.assigned.reviewed().values('reviewer')
        reviewers = self.reviewers.exclude(id__in=reviewers_submitted)
        return reviewers

    @property
    def staff_not_reviewed(self):
        return self.missing_reviewers.staff()

    @property
    def reviewers_not_reviewed(self):
        return self.missing_reviewers.reviewers().exclude(id__in=self.staff_not_reviewed)

    def reviewed_by(self, user):
        return self.assigned.reviewed().filter(reviewer=user).exists()

    def flagged_by(self, user):
        return self.flags.filter(user=user, type=Flag.USER).exists()

    @property
    def flagged_staff(self):
        return self.flags.filter(type=Flag.STAFF).exists()

    def has_permission_to_review(self, user):
        if user.is_apply_staff:
            return True

        if user in self.reviewers_not_reviewed:
            return True

        if user.is_community_reviewer and self.user != user and self.community_review and not self.reviewed_by(user):
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

    @property
    def ready_for_determination(self):
        return self.status in PHASES_MAPPING['ready-for-determination']['statuses']

    @property
    def accepted_for_funding(self):
        accepted = self.status in PHASES_MAPPING['accepted']['statuses']
        return self.in_final_stage and accepted

    @property
    def in_final_stage(self):
        stages = self.workflow.stages

        stage_index = stages.index(self.stage)

        # adjust the index since list.index() is zero-based
        adjusted_index = stage_index + 1

        return adjusted_index == len(stages)

    @property
    def in_internal_review_phase(self):
        return self.status in PHASES_MAPPING['internal-review']['statuses']

    @property
    def in_external_review_phase(self):
        return self.status in PHASES_MAPPING['external-review']['statuses']

    @property
    def is_finished(self):
        accepted = self.status in PHASES_MAPPING['accepted']['statuses']
        dismissed = self.status in PHASES_MAPPING['dismissed']['statuses']
        return accepted or dismissed

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
        return self.data(name)

    @property
    def has_default_screening_status_set(self):
        return self.screening_statuses.filter(default=True).exists()

    @property
    def has_yes_default_screening_status_set(self):
        return self.screening_statuses.filter(default=True, yes=True).exists()

    @property
    def has_no_default_screening_status_set(self):
        return self.screening_statuses.filter(default=True, yes=False).exists()

    @property
    def can_not_edit_default(self):
        return self.screening_statuses.all().count() > 1

    @property
    def joined_screening_statuses(self):
        return ', '.join([s.title for s in self.screening_statuses.all()])

    @property
    def yes_screening_statuses(self):
        ScreeningStatus = apps.get_model('funds', 'ScreeningStatus')
        return json.dumps(
            {status.title: status.id for status in ScreeningStatus.objects.filter(yes=True)}
        )

    @property
    def no_screening_statuses(self):
        ScreeningStatus = apps.get_model('funds', 'ScreeningStatus')
        return json.dumps(
            {status.title: status.id for status in ScreeningStatus.objects.filter(yes=False)}
        )

    @property
    def supports_default_screening(self):
        if self.screening_statuses.exists():
            return self.screening_statuses.filter(default=True).exists()
        return True


@receiver(post_transition, sender=ApplicationSubmission)
def log_status_update(sender, **kwargs):
    instance = kwargs['instance']
    old_phase = instance.workflow[kwargs['source']]

    by = kwargs['method_kwargs']['by']
    request = kwargs['method_kwargs']['request']
    notify = kwargs['method_kwargs'].get('notify', True)

    if request and notify:
        if kwargs['source'] == DRAFT_STATE:
            messenger(
                MESSAGES.NEW_SUBMISSION,
                request=request,
                user=by,
                source=instance,
            )
        else:
            messenger(
                MESSAGES.TRANSITION,
                user=by,
                request=request,
                source=instance,
                related=old_phase,
            )

        if instance.status in review_statuses:
            messenger(
                MESSAGES.READY_FOR_REVIEW,
                user=by,
                request=request,
                source=instance,
            )

    if instance.status in STAGE_CHANGE_ACTIONS:
        messenger(
            MESSAGES.INVITED_TO_PROPOSAL,
            request=request,
            user=by,
            source=instance,
        )


class ApplicationRevision(BaseStreamForm, AccessFormData, models.Model):
    submission = models.ForeignKey(ApplicationSubmission, related_name='revisions', on_delete=models.CASCADE)
    form_data = models.JSONField(encoder=StreamFieldDataEncoder)
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
    def review_order(self):
        review_order = [
            STAFF_GROUP_NAME,
            COMMUNITY_REVIEWER_GROUP_NAME,
            REVIEWER_GROUP_NAME,
        ]

        ordering = [
            models.When(type__name=review_type, then=models.Value(i))
            for i, review_type in enumerate(review_order)
        ]
        return self.exclude(
            # Remove people from the list who are opinionated but
            # didn't review, they appear elsewhere
            opinions__isnull=False,
            review__isnull=True,
        ).annotate(
            type_order=models.Case(
                *ordering,
                output_field=models.IntegerField(),
            ),
            has_review=models.Case(
                models.When(review__isnull=True, then=models.Value(1)),
                models.When(review__is_draft=True, then=models.Value(1)),
                default=models.Value(0),
                output_field=models.IntegerField(),
            )
        ).order_by(
            'type_order',
            'has_review',
            F('role__order').asc(nulls_last=True),
        ).select_related(
            'reviewer',
            'role',
        )

    def with_roles(self):
        return self.filter(role__isnull=False)

    def without_roles(self):
        return self.filter(role__isnull=True)

    def reviewed(self):
        return self.filter(
            Q(opinions__opinion=AGREE) |
            Q(Q(review__isnull=False) & Q(review__is_draft=False))
        ).distinct()

    def draft_reviewed(self):
        return self.filter(
            Q(Q(review__isnull=False) & Q(review__is_draft=True))
        ).distinct()

    def not_reviewed(self):
        return self.filter(
            Q(review__isnull=True) | Q(review__is_draft=True),
            Q(opinions__isnull=True) | Q(opinions__opinion=DISAGREE),
        ).distinct()

    def never_tried_to_review(self):
        # Different from not reviewed as draft reviews allowed
        return self.filter(
            review__isnull=True,
            opinions__isnull=True,
        )

    def staff(self):
        return self.filter(type__name=STAFF_GROUP_NAME)

    def get_or_create_for_user(self, submission, reviewer):
        groups = set(reviewer.groups.values_list('name', flat=True)) & set(REVIEW_GROUPS)
        if len(groups) > 1:
            if COMMUNITY_REVIEWER_GROUP_NAME in groups:
                groups = {COMMUNITY_REVIEWER_GROUP_NAME}
            elif reviewer.is_apply_staff:
                groups = {STAFF_GROUP_NAME}
            else:
                groups = {REVIEWER_GROUP_NAME}
        elif not groups:
            if reviewer.is_staff or reviewer.is_superuser:
                groups = {STAFF_GROUP_NAME}
            else:
                groups = {REVIEWER_GROUP_NAME}

        group = Group.objects.get(name=groups.pop())

        return self.get_or_create(
            submission=submission,
            reviewer=reviewer,
            type=group,
        )

    def get_or_create_staff(self, submission, reviewer):
        return self.get_or_create(
            submission=submission,
            reviewer=reviewer,
            type=Group.objects.get(name=STAFF_GROUP_NAME),
        )

    def bulk_create_reviewers(self, reviewers, submission):
        group = Group.objects.get(name=REVIEWER_GROUP_NAME)
        self.bulk_create(
            [
                self.model(
                    submission=submission,
                    role=None,
                    reviewer=reviewer,
                    type=group,
                ) for reviewer in reviewers
            ],
            ignore_conflicts=True
        )

    def update_role(self, role, reviewer, *submissions):
        # Remove role who didn't review
        self.filter(submission__in=submissions, role=role).never_tried_to_review().delete()
        # Anyone else we remove their role
        self.filter(submission__in=submissions, role=role).update(role=None)
        # Create/update the new role reviewers
        group = Group.objects.get(name=STAFF_GROUP_NAME)
        for submission in submissions:
            self.update_or_create(
                submission=submission,
                reviewer=reviewer,
                defaults={'role': role, 'type': group},
            )


class AssignedReviewers(models.Model):
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to=LIMIT_TO_REVIEWER_GROUPS,
    )
    type = models.ForeignKey(
        'auth.Group',
        on_delete=models.PROTECT,
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
        unique_together = (('submission', 'role'), ('submission', 'reviewer'))

    def __hash__(self):
        return hash(self.pk)

    def __str__(self):
        return f'{self.reviewer}'

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
