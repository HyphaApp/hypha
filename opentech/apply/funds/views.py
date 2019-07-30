from copy import copy

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView, DeleteView

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from wagtail.core.models import Page

from opentech.apply.activity.views import (
    AllActivityContextMixin,
    ActivityContextMixin,
    CommentFormView,
    DelegatedViewMixin,
)
from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.determinations.views import BatchDeterminationCreateView, DeterminationCreateOrUpdateView
from opentech.apply.projects.forms import CreateProjectForm
from opentech.apply.projects.models import Project
from opentech.apply.review.views import ReviewContextMixin
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.storage import PrivateMediaView
from opentech.apply.utils.views import DelegateableListView, DelegateableView, ViewDispatcher

from .differ import compare
from .files import generate_submission_file_path
from .forms import (
    BatchUpdateSubmissionLeadForm,
    BatchUpdateReviewersForm,
    BatchProgressSubmissionForm,
    ProgressSubmissionForm,
    ScreeningSubmissionForm,
    UpdateReviewersForm,
    UpdateSubmissionLeadForm,
    UpdatePartnersForm,
    UpdateMetaTermsForm,
)
from .models import (
    ApplicationSubmission,
    ApplicationRevision,
    RoundsAndLabs,
    RoundBase,
    LabBase
)
from .paginators import LazyPaginator
from .permissions import is_user_has_access_to_view_submission
from .tables import (
    AdminSubmissionsTable,
    ReviewerSubmissionsTable,
    RoundsTable,
    RoundsFilter,
    SubmissionFilterAndSearch,
    SubmissionReviewerFilterAndSearch,
    SummarySubmissionsTable,
)
from .workflow import INITIAL_STATE, STAGE_CHANGE_ACTIONS, PHASES_MAPPING, review_statuses


class BaseAdminSubmissionsTable(SingleTableMixin, FilterView):
    table_class = AdminSubmissionsTable
    filterset_class = SubmissionFilterAndSearch
    filter_action = ''
    table_pagination = {'klass': LazyPaginator}

    excluded_fields = []

    @property
    def excluded(self):
        return {
            'exclude': self.excluded_fields
        }

    def get_table_kwargs(self, **kwargs):
        return {**self.excluded, **kwargs}

    def get_filterset_kwargs(self, filterset_class, **kwargs):
        new_kwargs = super().get_filterset_kwargs(filterset_class)
        new_kwargs.update(self.excluded)
        new_kwargs.update(kwargs)
        return new_kwargs

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current().for_table(self.request.user)

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')

        return super().get_context_data(
            search_term=search_term,
            filter_action=self.filter_action,
            **kwargs,
        )


@method_decorator(staff_required, name='dispatch')
class BatchUpdateLeadView(DelegatedViewMixin, FormView):
    form_class = BatchUpdateSubmissionLeadForm
    context_name = 'batch_lead_form'

    def form_valid(self, form):
        new_lead = form.cleaned_data['lead']
        submissions = form.cleaned_data['submissions']
        form.save()

        messenger(
            MESSAGES.BATCH_UPDATE_LEAD,
            request=self.request,
            user=self.request.user,
            sources=submissions,
            new_lead=new_lead,
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, mark_safe(_('Sorry something went wrong') + form.errors.as_ul()))
        return super().form_invalid(form)


@method_decorator(staff_required, name='dispatch')
class BatchUpdateReviewersView(DelegatedViewMixin, FormView):
    form_class = BatchUpdateReviewersForm
    context_name = 'batch_reviewer_form'

    def form_valid(self, form):
        submissions = form.cleaned_data['submissions']
        form.save()
        reviewers = [
            [role, form.cleaned_data[field_name]]
            for field_name, role in form.role_fields.items()
        ]

        messenger(
            MESSAGES.BATCH_REVIEWERS_UPDATED,
            request=self.request,
            user=self.request.user,
            sources=submissions,
            added=reviewers,
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, mark_safe(_('Sorry something went wrong') + form.errors.as_ul()))
        return super().form_invalid(form)


@method_decorator(staff_required, name='dispatch')
class BatchProgressSubmissionView(DelegatedViewMixin, FormView):
    form_class = BatchProgressSubmissionForm
    context_name = 'batch_progress_form'

    def form_valid(self, form):
        submissions = form.cleaned_data['submissions']
        transitions = form.cleaned_data.get('action')

        try:
            redirect = BatchDeterminationCreateView.should_redirect(self.request, submissions, transitions)
        except ValueError as e:
            messages.warning(self.request, 'Could not determine: ' + str(e))
            return self.form_invalid(form)
        else:
            if redirect:
                return redirect

        failed = []
        phase_changes = {}
        for submission in submissions:
            valid_actions = {action for action, _ in submission.get_actions_for_user(self.request.user)}
            old_phase = submission.phase
            try:
                transition = (valid_actions & set(transitions)).pop()
                submission.perform_transition(
                    transition,
                    self.request.user,
                    request=self.request,
                    notify=False,
                )
            except (PermissionDenied, KeyError):
                failed.append(submission)
            else:
                phase_changes[submission.id] = old_phase

        if failed:
            messages.warning(
                self.request,
                _('Failed to update: ') +
                ', '.join(str(submission) for submission in failed)
            )

        succeeded_submissions = submissions.exclude(id__in=[submission.id for submission in failed])
        messenger(
            MESSAGES.BATCH_TRANSITION,
            user=self.request.user,
            request=self.request,
            sources=succeeded_submissions,
            related=phase_changes,
        )

        ready_for_review = [
            phase for phase in transitions
            if phase in review_statuses
        ]
        if ready_for_review:
            messenger(
                MESSAGES.BATCH_READY_FOR_REVIEW,
                user=self.request.user,
                request=self.request,
                sources=succeeded_submissions.filter(status__in=ready_for_review),
            )

        return super().form_valid(form)


class BaseReviewerSubmissionsTable(BaseAdminSubmissionsTable):
    table_class = ReviewerSubmissionsTable
    filterset_class = SubmissionReviewerFilterAndSearch

    def get_queryset(self):
        # Reviewers can only see submissions they have reviewed
        return super().get_queryset().reviewed_by(self.request.user)


@method_decorator(staff_required, name='dispatch')
class SubmissionOverviewView(AllActivityContextMixin, BaseAdminSubmissionsTable):
    template_name = 'funds/submissions_overview.html'
    table_class = SummarySubmissionsTable
    table_pagination = False
    filter_action = reverse_lazy('funds:submissions:list')

    def get_table_data(self):
        return super().get_table_data().order_by(F('last_update').desc(nulls_last=True))[:5]

    def get_context_data(self, **kwargs):
        base_query = RoundsAndLabs.objects.with_progress().active().order_by('-end_date')
        open_rounds = base_query.open()[:6]
        open_query = '?round_state=open'
        closed_rounds = base_query.closed()[:6]
        closed_query = '?round_state=closed'
        rounds_title = 'All Rounds and Labs'

        status_counts = dict(
            ApplicationSubmission.objects.current().values('status').annotate(
                count=Count('status'),
            ).values_list('status', 'count')
        )

        grouped_statuses = {
            status: {
                'name': data['name'],
                'count': sum(status_counts.get(status, 0) for status in data['statuses']),
                'url': reverse_lazy("funds:submissions:status", kwargs={'status': status})
            }
            for status, data in PHASES_MAPPING.items()
        }

        return super().get_context_data(
            open_rounds=open_rounds,
            open_query=open_query,
            closed_rounds=closed_rounds,
            closed_query=closed_query,
            rounds_title=rounds_title,
            status_counts=grouped_statuses,
            **kwargs,
        )


class SubmissionAdminListView(AllActivityContextMixin, BaseAdminSubmissionsTable, DelegateableListView):
    template_name = 'funds/submissions.html'
    form_views = [
        BatchUpdateLeadView,
        BatchUpdateReviewersView,
        BatchProgressSubmissionView,
    ]


class SubmissionReviewerListView(AllActivityContextMixin, BaseReviewerSubmissionsTable):
    template_name = 'funds/submissions.html'


class SubmissionListView(ViewDispatcher):
    admin_view = SubmissionAdminListView
    reviewer_view = SubmissionReviewerListView


@method_decorator(staff_required, name='dispatch')
class SubmissionsByRound(AllActivityContextMixin, BaseAdminSubmissionsTable, DelegateableListView):
    template_name = 'funds/submissions_by_round.html'
    form_views = [
        BatchUpdateLeadView,
        BatchUpdateReviewersView,
        BatchProgressSubmissionView,
    ]

    excluded_fields = ('round', 'lead', 'fund')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['round'] = self.obj
        return kwargs

    def get_queryset(self):
        # We want to only show lab or Rounds in this view, their base class is Page
        try:
            self.obj = Page.objects.get(pk=self.kwargs.get('pk')).specific
        except Page.DoesNotExist:
            raise Http404(_("No Round or Lab found matching the query"))

        if not isinstance(self.obj, (LabBase, RoundBase)):
            raise Http404(_("No Round or Lab found matching the query"))
        return super().get_queryset().filter(Q(round=self.obj) | Q(page=self.obj))

    def get_context_data(self, **kwargs):
        return super().get_context_data(object=self.obj, **kwargs)


@method_decorator(staff_required, name='dispatch')
class SubmissionsByStatus(BaseAdminSubmissionsTable, DelegateableListView):
    template_name = 'funds/submissions_by_status.html'
    status_mapping = PHASES_MAPPING
    form_views = [
        BatchUpdateLeadView,
        BatchUpdateReviewersView,
        BatchProgressSubmissionView,
    ]

    def dispatch(self, request, *args, **kwargs):
        self.status = kwargs.get('status')
        try:
            status_data = self.status_mapping[self.status]
        except KeyError:
            raise Http404(_("No statuses match the requested value"))
        self.status_name = status_data['name']
        self.statuses = status_data['statuses']
        return super().dispatch(request, *args, **kwargs)

    def get_filterset_kwargs(self, filterset_class, **kwargs):
        return super().get_filterset_kwargs(filterset_class, limit_statuses=self.statuses, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(status__in=self.statuses)

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            status=self.status_name,
            statuses=self.statuses,
            **kwargs,
        )


@method_decorator(staff_required, name='dispatch')
class ProgressSubmissionView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = ProgressSubmissionForm
    context_name = 'progress_form'

    def form_valid(self, form):
        action = form.cleaned_data.get('action')
        # Defer to the determination form for any of the determination transitions
        redirect = DeterminationCreateOrUpdateView.should_redirect(self.request, self.object, action)
        if redirect:
            return redirect

        self.object.perform_transition(action, self.request.user, request=self.request)
        return super().form_valid(form)


@method_decorator(staff_required, name='dispatch')
class CreateProjectView(DelegatedViewMixin, CreateView):
    context_name = 'project_form'
    form_class = CreateProjectForm
    model = Project

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.CREATED_PROJECT,
            request=self.request,
            user=self.request.user,
            source=self.object,
            related=self.object.submission,
        )

        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


@method_decorator(staff_required, name='dispatch')
class ScreeningSubmissionView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = ScreeningSubmissionForm
    context_name = 'screening_form'

    def form_valid(self, form):
        old = copy(self.get_object())
        response = super().form_valid(form)
        # Record activity
        messenger(
            MESSAGES.SCREENING,
            request=self.request,
            user=self.request.user,
            source=self.object,
            related=str(old.screening_status),
        )
        return response


@method_decorator(staff_required, name='dispatch')
class UpdateLeadView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = UpdateSubmissionLeadForm
    context_name = 'lead_form'

    def form_valid(self, form):
        # Fetch the old lead from the database
        old = copy(self.get_object())
        response = super().form_valid(form)
        messenger(
            MESSAGES.UPDATE_LEAD,
            request=self.request,
            user=self.request.user,
            source=form.instance,
            related=old.lead,
        )
        return response


@method_decorator(staff_required, name='dispatch')
class UpdateReviewersView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = UpdateReviewersForm
    context_name = 'reviewer_form'

    def form_valid(self, form):
        old_reviewers = set(
            copy(reviewer)
            for reviewer in form.instance.assigned.all()
        )
        response = super().form_valid(form)

        new_reviewers = set(form.instance.assigned.all())
        added = new_reviewers - old_reviewers
        removed = old_reviewers - new_reviewers

        messenger(
            MESSAGES.REVIEWERS_UPDATED,
            request=self.request,
            user=self.request.user,
            source=self.kwargs['object'],
            added=added,
            removed=removed,
        )

        if added:
            # Automatic workflow actions.
            action = None
            if self.object.status == INITIAL_STATE:
                # Automatically transition the application to "Internal review".
                action = self.object.workflow.stepped_phases[1][0].name
            elif self.object.status == 'proposal_discussion':
                # Automatically transition the proposal to "Internal review".
                action = 'proposal_internal_review'

            # If action is set run perform_transition().
            if action:
                try:
                    self.object.perform_transition(
                        action,
                        self.request.user,
                        request=self.request,
                        notify=False,
                    )
                except (PermissionDenied, KeyError):
                    pass

        return response


@method_decorator(staff_required, name='dispatch')
class UpdatePartnersView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = UpdatePartnersForm
    context_name = 'partner_form'

    def form_valid(self, form):
        old_partners = set(self.get_object().partners.all())
        response = super().form_valid(form)
        new_partners = set(form.instance.partners.all())

        added = new_partners - old_partners
        removed = old_partners - new_partners

        messenger(
            MESSAGES.PARTNERS_UPDATED,
            request=self.request,
            user=self.request.user,
            source=self.kwargs['object'],
            added=added,
            removed=removed,
        )

        messenger(
            MESSAGES.PARTNERS_UPDATED_PARTNER,
            request=self.request,
            user=self.request.user,
            source=self.kwargs['object'],
            added=added,
            removed=removed,
        )

        return response


@method_decorator(staff_required, name='dispatch')
class UpdateMetaTermsView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = UpdateMetaTermsForm
    context_name = 'meta_terms_form'


class AdminSubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_admin_detail'
    model = ApplicationSubmission
    form_views = [
        ProgressSubmissionView,
        ScreeningSubmissionView,
        CommentFormView,
        UpdateLeadView,
        UpdateReviewersView,
        UpdatePartnersView,
        CreateProjectView,
        UpdateMetaTermsView,
    ]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        redirect = SubmissionSealedView.should_redirect(request, submission)
        return redirect or super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        other_submissions = self.model.objects.filter(user=self.object.user).current().exclude(id=self.object.id)
        if self.object.next:
            other_submissions = other_submissions.exclude(id=self.object.next.id)

        public_page = self.object.get_from_parent('detail')()

        return super().get_context_data(
            other_submissions=other_submissions,
            public_page=public_page,
            **kwargs,
        )


class ReviewerSubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_reviewer_detail'
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers and partners may somtimes be appliants as well.
        if submission.user == request.user:
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)


class PartnerSubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_partner_detail'
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers and partners may somtimes be appliants as well.
        if submission.user == request.user:
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        # Only allow partners in the submission they are added as partners
        partner_has_access = submission.partners.filter(pk=request.user.pk).exists()
        if not partner_has_access:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class CommunitySubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_community_detail'
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers and partners may somtimes be appliants as well.
        if submission.user == request.user:
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        # Only allow community reviewers in submission with a community review state.
        if not submission.community_review:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ApplicantSubmissionDetailView(ActivityContextMixin, DelegateableView, DetailView):
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def get_object(self):
        return super().get_object().from_draft()

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # This view is only for applicants.
        if submission.user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SubmissionDetailView(ViewDispatcher):
    admin_view = AdminSubmissionDetailView
    reviewer_view = ReviewerSubmissionDetailView
    partner_view = PartnerSubmissionDetailView
    community_view = CommunitySubmissionDetailView
    applicant_view = ApplicantSubmissionDetailView


@method_decorator(staff_required, 'dispatch')
class SubmissionSealedView(DetailView):
    template_name = 'funds/submission_sealed.html'
    model = ApplicationSubmission

    def get(self, request, *args, **kwargs):
        submission = self.get_object()
        if not self.round_is_sealed(submission):
            return self.redirect_detail(submission)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        submission = self.get_object()
        if self.can_view_sealed(request.user):
            self.peeked(submission)
        return self.redirect_detail(submission)

    def redirect_detail(self, submission):
        return HttpResponseRedirect(reverse_lazy('funds:submissions:detail', args=(submission.id,)))

    def peeked(self, submission):
        messenger(
            MESSAGES.OPENED_SEALED,
            request=self.request,
            user=self.request.user,
            source=submission,
        )
        self.request.session.setdefault('peeked', {})[str(submission.id)] = True
        # Dictionary updates do not trigger session saves. Force update
        self.request.session.modified = True

    def can_view_sealed(self, user):
        return user.is_superuser

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            can_view_sealed=self.can_view_sealed(self.request.user),
            **kwargs,
        )

    @classmethod
    def round_is_sealed(cls, submission):
        try:
            return submission.round.specific.is_sealed
        except AttributeError:
            # Its a lab - cant be sealed
            return False

    @classmethod
    def has_peeked(cls, request, submission):
        return str(submission.id) in request.session.get('peeked', {})

    @classmethod
    def should_redirect(cls, request, submission):
        if cls.round_is_sealed(submission) and not cls.has_peeked(request, submission):
            return HttpResponseRedirect(reverse_lazy('funds:submissions:sealed', args=(submission.id,)))


class BaseSubmissionEditView(UpdateView):
    """
    Converts the data held on the submission into an editable format and knows how to save
    that back to the object. Shortcuts the normal update view save approach
    """
    model = ApplicationSubmission

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().phase.permissions.can_edit(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def buttons(self):
        yield ('save', 'white', 'Save Draft')
        yield ('submit', 'primary', 'Submit')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.pop('instance').from_draft()
        kwargs['initial'] = instance.raw_data
        return kwargs

    def get_context_data(self, **kwargs):
        return super().get_context_data(buttons=self.buttons(), **kwargs)

    def get_form_class(self):
        return self.object.get_form_class()


@method_decorator(staff_required, name='dispatch')
class AdminSubmissionEditView(BaseSubmissionEditView):
    def form_valid(self, form):
        self.object.new_data(form.cleaned_data)

        if 'save' in self.request.POST:
            self.object.create_revision(draft=True, by=self.request.user)
            return self.form_invalid(form)

        if 'submit' in self.request.POST:
            revision = self.object.create_revision(by=self.request.user)
            if revision:
                messenger(
                    MESSAGES.EDIT,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                    related=revision,
                )

        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class ApplicantSubmissionEditView(BaseSubmissionEditView):
    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        if request.user != submission.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    @property
    def transitions(self):
        transitions = self.object.get_available_user_status_transitions(self.request.user)
        return {
            transition.name: transition
            for transition in transitions
        }

    def form_valid(self, form):
        self.object.new_data(form.cleaned_data)

        if 'save' in self.request.POST:
            self.object.create_revision(draft=True, by=self.request.user)
            messages.success(self.request, _('Submission saved successfully'))
            return self.form_invalid(form)

        revision = self.object.create_revision(by=self.request.user)
        submitting_proposal = self.object.phase.name in STAGE_CHANGE_ACTIONS

        if submitting_proposal:
            messenger(
                MESSAGES.PROPOSAL_SUBMITTED,
                request=self.request,
                user=self.request.user,
                source=self.object,
            )
        elif revision:
            messenger(
                MESSAGES.APPLICANT_EDIT,
                request=self.request,
                user=self.request.user,
                source=self.object,
                related=revision,
            )

        action = set(self.request.POST.keys()) & set(self.transitions.keys())
        try:
            transition = self.transitions[action.pop()]
        except KeyError:
            pass
        else:
            self.object.perform_transition(
                transition.target,
                self.request.user,
                request=self.request,
                notify=not (revision or submitting_proposal),  # Use the other notification
            )

        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class PartnerSubmissionEditView(ApplicantSubmissionEditView):
    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Partners may somtimes be appliants as well.
        partner_has_access = submission.partners.filter(pk=request.user.pk).exists()
        if not partner_has_access and submission.user != request.user:
            raise PermissionDenied
        return super(ApplicantSubmissionEditView, self).dispatch(request, *args, **kwargs)


class SubmissionEditView(ViewDispatcher):
    admin_view = AdminSubmissionEditView
    applicant_view = ApplicantSubmissionEditView
    reviewer_view = ApplicantSubmissionEditView
    partner_view = PartnerSubmissionEditView


@method_decorator(staff_required, name='dispatch')
class RevisionListView(ListView):
    model = ApplicationRevision

    def get_queryset(self):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        self.queryset = self.model.objects.filter(
            submission=self.submission,
        ).exclude(
            draft__isnull=False,
            live__isnull=True,
        )
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            submission=self.submission,
            **kwargs,
        )


@method_decorator(staff_required, name='dispatch')
class RevisionCompareView(DetailView):
    model = ApplicationSubmission
    template_name = 'funds/revisions_compare.html'
    pk_url_kwarg = 'submission_pk'

    def compare_revisions(self, from_data, to_data):
        self.object.form_data = from_data.form_data
        from_rendered_text_fields = self.object.render_text_blocks_answers()
        from_required = self.render_required()

        self.object.form_data = to_data.form_data
        to_rendered_text_fields = self.object.render_text_blocks_answers()
        to_required = self.render_required()

        required_fields = [
            compare(*fields)
            for fields in zip(from_required, to_required)
        ]

        stream_fields = [
            compare(*fields)
            for fields in zip(from_rendered_text_fields, to_rendered_text_fields)
        ]

        return (required_fields, stream_fields)

    def render_required(self):
        return [
            getattr(self.object, 'get_{}_display'.format(field))()
            for field in self.object.named_blocks
        ]

    def get_context_data(self, **kwargs):
        from_revision = self.object.revisions.get(id=self.kwargs['from'])
        to_revision = self.object.revisions.get(id=self.kwargs['to'])
        required_fields, stream_fields = self.compare_revisions(from_revision, to_revision)
        timestamps = (from_revision.timestamp, to_revision.timestamp)
        return super().get_context_data(
            timestamps=timestamps,
            required_fields=required_fields,
            stream_fields=stream_fields,
            **kwargs,
        )


@method_decorator(staff_required, name='dispatch')
class RoundListView(SingleTableMixin, FilterView):
    template_name = 'funds/rounds.html'
    table_class = RoundsTable
    filterset_class = RoundsFilter

    def get_queryset(self):
        return RoundsAndLabs.objects.with_progress()


@method_decorator(permission_required('funds.delete_applicationsubmission', raise_exception=True), name='dispatch')
class SubmissionDeleteView(DeleteView):
    model = ApplicationSubmission
    success_url = reverse_lazy('funds:submissions:list')

    def delete(self, request, *args, **kwargs):
        submission = self.get_object()
        messenger(
            MESSAGES.DELETE_SUBMISSION,
            user=request.user,
            request=request,
            source=submission,
        )
        response = super().delete(request, *args, **kwargs)
        return response


@method_decorator(login_required, name='dispatch')
class SubmissionPrivateMediaView(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        submission_pk = self.kwargs['pk']
        self.submission = get_object_or_404(ApplicationSubmission, pk=submission_pk)
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        field_id = kwargs['field_id']
        file_name = kwargs['file_name']
        path_to_file = generate_submission_file_path(self.submission.pk, field_id, file_name)
        return self.storage.open(path_to_file)

    def test_func(self):
        return is_user_has_access_to_view_submission(self.request.user, self.submission)


@method_decorator(staff_required, name='dispatch')
class SubmissionDetailSimplifiedView(DetailView):
    model = ApplicationSubmission
    template_name_suffix = '_simplified_detail'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if not hasattr(obj, 'project'):
            raise Http404

        return obj
