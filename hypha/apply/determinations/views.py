from urllib import parse

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, UpdateView
from wagtail.core.models import Site

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import Activity
from hypha.apply.funds.models import ApplicationSubmission
from hypha.apply.funds.workflow import DETERMINATION_OUTCOMES
from hypha.apply.projects.models import Project
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.users.decorators import staff_required
from hypha.apply.utils.views import CreateOrUpdateView, ViewDispatcher

from .blocks import DeterminationBlock
from .forms import (
    BatchConceptDeterminationForm,
    BatchDeterminationForm,
    BatchProposalDeterminationForm,
    ConceptDeterminationForm,
    DeterminationModelForm,
    ProposalDeterminationForm,
)
from .models import Determination, DeterminationMessageSettings
from .options import DETERMINATION_CHOICES, NEEDS_MORE_INFO, TRANSITION_DETERMINATION
from .utils import (
    can_create_determination,
    can_edit_determination,
    determination_actions,
    has_final_determination,
    outcome_from_actions,
    transition_from_outcome,
)


def get_form_for_stages(submissions):
    forms = [
        get_form_for_stage(submission, batch=True)
        for submission in submissions
    ]
    if len(set(forms)) != 1:
        raise ValueError('Submissions expect different forms - please contact admin')

    return forms[0]


def get_form_for_stage(submission, batch=False, edit=False):
    if batch:
        forms = [BatchConceptDeterminationForm, BatchProposalDeterminationForm]
    else:
        forms = [ConceptDeterminationForm, ProposalDeterminationForm]
    index = submission.workflow.stages.index(submission.stage)
    return forms[index]


def get_fields_for_stages(submissions):
    forms_fields = [
        get_fields_for_stage(submission)
        for submission in submissions
    ]
    if not all(i == forms_fields[0] for i in forms_fields):
        raise ValueError('Submissions expect different forms - please contact admin')
    return forms_fields[0]


def get_fields_for_stage(submission):
    forms = submission.get_from_parent('determination_forms').all()
    index = submission.workflow.stages.index(submission.stage)
    try:
        return forms[index].form.form_fields
    except IndexError:
        return forms[0].form.form_fields


def outcome_choices_for_phase(submission, user):
    """
    Outcome choices correspond to Phase transitions.
    We need to filter out non-matching choices.
    i.e. a transition to In Review is not a determination, while Needs more info or Rejected are.
    """
    available_choices = set()
    choices = dict(DETERMINATION_CHOICES)
    for transition_name in determination_actions(user, submission):
        try:
            determination_type = TRANSITION_DETERMINATION[transition_name]
        except KeyError:
            pass
        else:
            available_choices.add((determination_type, choices[determination_type]))

    return available_choices


@method_decorator(staff_required, name='dispatch')
class BatchDeterminationCreateView(BaseStreamForm, CreateView):
    submission_form_class = BatchDeterminationForm
    template_name = 'determinations/batch_determination_form.html'

    def dispatch(self, *args, **kwargs):
        self._submissions = None
        if not self.get_action() or not self.get_submissions():
            messages.warning(self.request, 'Improperly configured request, please try again.')
            return HttpResponseRedirect(self.get_success_url())

        return super().dispatch(*args, **kwargs)

    def get_action(self):
        return self.request.GET.get('action', '')

    def get_submissions(self):
        if not self._submissions:
            try:
                submission_ids = self.request.GET.get('submissions').split(',')
            except AttributeError:
                return None
            try:
                ids = [int(pk) for pk in submission_ids]
            except ValueError:
                return None
            self._submissions = ApplicationSubmission.objects.filter(id__in=ids)
        return self._submissions

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['submissions'] = self.get_submissions()
        kwargs['action'] = self.get_action()
        kwargs['site'] = Site.find_for_request(self.request)
        kwargs.pop('instance')
        return kwargs

    def check_all_submissions_are_of_same_type(self, submissions):
        """
        Checks if all the submission as the new determination form attached to it.

        Or all should be using the old determination forms.

        We can not create batch determination with submissions using two different
        type of forms.
        """
        return len(set(
            [
                submission.is_determination_form_attached
                for submission in submissions
            ]
        )) == 1

    def get_form_class(self):
        submissions = self.get_submissions()
        if not self.check_all_submissions_are_of_same_type(submissions):
            raise ValueError(
                "All selected submissions excpects determination forms attached"
                " - please contact admin"
            )
        if not submissions[0].is_determination_form_attached:
            # If all the submission has same type of forms but they are not the
            # new streamfield forms then use the old determination forms.
            return get_form_for_stages(submissions)
        form_fields = self.get_form_fields()
        field_blocks = self.get_defined_fields()
        for field_block in field_blocks:
            if isinstance(field_block.block, DeterminationBlock):
                # Outcome is already set in case of batch determinations so we do
                # not need to render this field.
                form_fields.pop(field_block.id)
        return type('WagtailStreamForm', (self.submission_form_class,), form_fields)

    def get_defined_fields(self):
        return get_fields_for_stages(self.get_submissions())

    def get_context_data(self, **kwargs):
        outcome = TRANSITION_DETERMINATION[self.get_action()]
        submission = self.get_submissions()[0]
        transition = transition_from_outcome(outcome, submission)
        action_name = submission.workflow[transition].display_name
        return super().get_context_data(
            action_name=action_name,
            submissions=self.get_submissions(),
            **kwargs,
        )

    def form_valid(self, form):
        submissions = self.get_submissions()
        response = super().form_valid(form)
        determinations = {
            determination.submission.id: determination
            for determination in form.instances
        }
        messenger(
            MESSAGES.BATCH_DETERMINATION_OUTCOME,
            request=self.request,
            user=self.request.user,
            sources=submissions.filter(id__in=list(determinations)),
            related=determinations,
        )

        for submission in submissions:
            try:
                determination = determinations[submission.id]
            except KeyError:
                messages.warning(
                    self.request,
                    'Unable to determine submission "{title}" as already determined'.format(title=submission.title),
                )
            else:
                if submission.is_determination_form_attached:
                    determination.form_fields = self.get_defined_fields()
                    determination.message = form.cleaned_data[determination.message_field.id]
                    determination.save()
                transition = transition_from_outcome(form.cleaned_data.get('outcome'), submission)

                if determination.outcome == NEEDS_MORE_INFO:
                    # We keep a record of the message sent to the user in the comment
                    Activity.comments.create(
                        message=determination.stripped_message,
                        timestamp=timezone.now(),
                        user=self.request.user,
                        source=submission,
                        related_object=determination,
                    )

                submission.perform_transition(transition, self.request.user, request=self.request, notify=False)
        return response

    @classmethod
    def should_redirect(cls, request, submissions, actions):
        excluded = []
        for submission in submissions:
            if has_final_determination(submission):
                excluded.append(submission)

        non_determine_states = set(actions) - set(DETERMINATION_OUTCOMES.keys())
        if not any(non_determine_states):
            if excluded:
                messages.warning(
                    request,
                    _('A determination already exists for the following submissions and they have been excluded: {submissions}').format(
                        submissions=', '.join([submission.title for submission in excluded]),
                    )
                )

            submissions = submissions.exclude(id__in=[submission.id for submission in excluded])
            action = outcome_from_actions(actions)
            return HttpResponseRedirect(
                reverse_lazy('apply:submissions:determinations:batch') +
                "?action=" + action +
                "&submissions=" + ','.join([str(submission.id) for submission in submissions]) +
                "&next=" + parse.quote_plus(request.get_full_path()),
            )
        elif set(actions) != non_determine_states:
            raise ValueError('Inconsistent states provided - please talk to an admin')

    def get_success_url(self):
        try:
            return self.request.GET['next']
        except KeyError:
            return reverse_lazy('apply:submissions:list')


@method_decorator(staff_required, name='dispatch')
class DeterminationCreateOrUpdateView(BaseStreamForm, CreateOrUpdateView):
    submission_form_class = DeterminationModelForm
    model = Determination
    template_name = 'determinations/determination_form.html'

    def get_object(self, queryset=None):
        return self.model.objects.get(submission=self.submission, is_draft=True)

    def dispatch(self, request, *args, **kwargs):

        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])

        if not can_create_determination(request.user, self.submission):
            return self.back_to_submission(_('You do not have permission to create that determination.'))

        if has_final_determination(self.submission):
            return self.back_to_submission(_('A final determination has already been submitted.'))

        try:
            self.determination = self.get_object()
        except Determination.DoesNotExist:
            pass
        else:
            if not can_edit_determination(request.user, self.determination, self.submission):
                return self.back_to_detail(_('There is a draft determination you do not have permission to edit.'))

        return super().dispatch(request, *args, **kwargs)

    def back_to_submission(self, message):
        messages.warning(self.request, message)
        return HttpResponseRedirect(self.submission.get_absolute_url())

    def back_to_detail(self, message):
        messages.warning(self.request, message)
        return HttpResponseRedirect(self.determination.get_absolute_url())

    def get_context_data(self, **kwargs):
        site = Site.find_for_request(self.request)
        determination_messages = DeterminationMessageSettings.for_site(site)

        # Create a dict that maps between opaque field ids
        # and canonical names for use in the template.
        # TODO: Put this functionality higher in the class hierarchy.
        determination_form_class = self.get_form_class()
        form_field_id_to_name = {}
        for field_id in determination_form_class.display:
            form_field_id_to_name[field_id] = determination_form_class.display[field_id].canonical_name

        return super().get_context_data(
            submission=self.submission,
            message_templates=determination_messages.get_for_stage(self.submission.stage.name),
            form_field_id_to_name=form_field_id_to_name,
            **kwargs
        )

    def get_defined_fields(self):
        return get_fields_for_stage(self.submission)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['submission'] = self.submission
        kwargs['action'] = self.request.GET.get('action')
        kwargs['site'] = Site.find_for_request(self.request)
        return kwargs

    def get_form_class(self):
        if not self.submission.is_determination_form_attached:
            # If new determination forms are not attached use the old ones.
            return get_form_for_stage(self.submission)
        form_fields = self.get_form_fields()
        field_blocks = self.get_defined_fields()
        for field_block in field_blocks:
            if isinstance(field_block.block, DeterminationBlock):
                outcome_choices = outcome_choices_for_phase(
                    self.submission, self.request.user
                )
                # Outcome field choices need to be set according to the phase.
                form_fields[field_block.id].choices = outcome_choices
        form_fields = self.add_proposal_form_field(form_fields)
        return type('WagtailStreamForm', (self.submission_form_class,), form_fields)

    def add_proposal_form_field(self, fields):
        action = self.request.GET.get('action')
        stages_num = len(self.submission.workflow.stages)
        if stages_num > 1 and action == 'invited_to_proposal':
            second_stage_forms = self.submission.get_from_parent('forms').filter(stage=2)
            if second_stage_forms.count() > 1:
                proposal_form_choices = [
                    (index, form.form.name)
                    for index, form in enumerate(second_stage_forms)
                ]
                fields['proposal_form'] = forms.ChoiceField(
                    label=_('Proposal Form'),
                    choices=proposal_form_choices,
                    help_text=_('Select the proposal form to use for proposal stage.'),
                )
                fields.move_to_end('proposal_form', last=False)
        return fields

    def get_success_url(self):
        return self.submission.get_absolute_url()

    def form_valid(self, form):
        if self.submission.is_determination_form_attached:
            form.instance.form_fields = self.get_defined_fields()

        super().form_valid(form)
        if self.object.is_draft:
            return HttpResponseRedirect(self.submission.get_absolute_url())

        with transaction.atomic():
            messenger(
                MESSAGES.DETERMINATION_OUTCOME,
                request=self.request,
                user=self.object.author,
                submission=self.object.submission,
                related=self.object,
            )
            proposal_form = form.cleaned_data.get('proposal_form')
            transition = transition_from_outcome(int(self.object.outcome), self.submission)

            if self.object.outcome == NEEDS_MORE_INFO:
                # We keep a record of the message sent to the user in the comment
                Activity.comments.create(
                    message=self.object.stripped_message,
                    timestamp=timezone.now(),
                    user=self.request.user,
                    source=self.submission,
                    related_object=self.object,
                )
            self.submission.perform_transition(
                transition,
                self.request.user,
                request=self.request,
                notify=False,
                proposal_form=proposal_form,
            )

            if self.submission.accepted_for_funding and settings.PROJECTS_AUTO_CREATE:
                project = Project.create_from_submission(self.submission)
                if project:
                    messenger(
                        MESSAGES.CREATED_PROJECT,
                        request=self.request,
                        user=self.request.user,
                        source=project,
                        related=project.submission,
                    )

        messenger(
            MESSAGES.DETERMINATION_OUTCOME,
            request=self.request,
            user=self.object.author,
            source=self.object.submission,
            related=self.object,
        )

        return HttpResponseRedirect(self.submission.get_absolute_url())

    @classmethod
    def should_redirect(cls, request, submission, action):
        if has_final_determination(submission):
            determination = submission.determinations.final().first()
            if determination.outcome == TRANSITION_DETERMINATION[action]:
                # We want to progress as normal so don't redirect through form
                return False
            else:
                if request:
                    # Add a helpful message to prompt them to select the correct option
                    messages.warning(
                        request,
                        _('A determination of "{current}" exists but you tried to progress as "{target}"').format(
                            current=determination.get_outcome_display(),
                            target=action,
                        )
                    )

        if action in DETERMINATION_OUTCOMES:
            return HttpResponseRedirect(reverse_lazy(
                'apply:submissions:determinations:form',
                args=(submission.id,)) + "?action=" + action
            )


@method_decorator(staff_required, name='dispatch')
class AdminDeterminationDetailView(DetailView):
    model = Determination

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, submission=self.submission, id=self.kwargs['pk'])

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        determination = self.get_object()

        if can_edit_determination(request.user, determination, self.submission) and determination.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:determinations:form', args=(self.submission.id,)))

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ReviewerDeterminationDetailView(DetailView):
    model = Determination

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, submission=self.submission, id=self.kwargs['pk'])

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        determination = self.get_object()

        if not determination.submitted:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:detail', args=(self.submission.id,)))

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class PartnerDeterminationDetailView(DetailView):
    model = Determination

    def get_queryset(self):
        return super().get_queryset().filter(submission=self.submission)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, pk=self.kwargs['submission_pk'])

        if self.submission.user == request.user:
            return ApplicantDeterminationDetailView.as_view()(request, *args, **kwargs)

        # Only allow partners in the submission they are added as partners
        partner_has_access = self.submission.partners.filter(pk=request.user.pk).exists()
        if not partner_has_access:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class CommunityDeterminationDetailView(DetailView):
    model = Determination

    def get_queryset(self):
        return super().get_queryset().filter(submission=self.submission)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, pk=self.kwargs['submission_pk'])

        if self.submission.user == request.user:
            return ApplicantDeterminationDetailView.as_view()(request, *args, **kwargs)

        # Only allow community reviewers in submission with a community review state.
        if not self.submission.community_review:
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name='dispatch')
class ApplicantDeterminationDetailView(DetailView):
    model = Determination

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, submission=self.submission, id=self.kwargs['pk'])

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        determination = self.get_object()

        if request.user != self.submission.user:
            raise PermissionDenied

        if determination.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:determinations:detail', args=(self.submission.id,)))

        return super().dispatch(request, *args, **kwargs)


class DeterminationDetailView(ViewDispatcher):
    admin_view = AdminDeterminationDetailView
    reviewer_view = ReviewerDeterminationDetailView
    partner_view = PartnerDeterminationDetailView
    community_view = CommunityDeterminationDetailView
    applicant_view = ApplicantDeterminationDetailView


@method_decorator(staff_required, name='dispatch')
class DeterminationEditView(BaseStreamForm, UpdateView):
    submission_form_class = DeterminationModelForm
    model = Determination
    template_name = 'determinations/determination_form.html'
    raise_exception = True

    def get_context_data(self, **kwargs):
        site = Site.find_for_request(self.request)
        determination_messages = DeterminationMessageSettings.for_site(site)

        determination = self.get_object()
        return super().get_context_data(
            submission=determination.submission,
            message_templates=determination_messages.get_for_stage(
                determination.submission.stage.name
            ),
            **kwargs
        )

    def get_defined_fields(self):
        determination = self.get_object()
        return get_fields_for_stage(determination.submission)

    def get_form_kwargs(self):
        determiantion = self.get_object()
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['submission'] = determiantion.submission
        kwargs['edit'] = True
        kwargs['action'] = self.request.GET.get('action')
        kwargs['site'] = Site.find_for_request(self.request)
        if self.object:
            kwargs['initial'] = self.object.form_data
        return kwargs

    def get_form_class(self):
        determination = self.get_object()
        if not determination.use_new_determination_form:
            return get_form_for_stage(determination.submission)
        form_fields = self.get_form_fields()
        field_blocks = self.get_defined_fields()
        for field_block in field_blocks:
            if isinstance(field_block.block, DeterminationBlock):
                # Outcome can not be edited after being set once, so we do not
                # need to render this field.
                form_fields.pop(field_block.id)
        return type('WagtailStreamForm', (self.submission_form_class,), form_fields)

    def form_valid(self, form):
        super().form_valid(form)
        determination = self.get_object()
        messenger(
            MESSAGES.DETERMINATION_OUTCOME,
            request=self.request,
            user=self.object.author,
            source=self.object.submission,
            related=self.object,
        )

        return HttpResponseRedirect(determination.submission.get_absolute_url())
