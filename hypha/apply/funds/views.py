from copy import copy
from datetime import timedelta

import django_tables2 as tables
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.exceptions import PermissionDenied
from django.db.models import Count, F, Q
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)
from django.views.generic.base import TemplateView
from django.views.generic.detail import SingleObjectMixin
from django_file_form.models import PlaceholderUploadedFile
from django_filters.views import FilterView
from django_tables2.paginators import LazyPaginator
from django_tables2.views import SingleTableMixin
from wagtail.core.models import Page

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.views import (
    ActivityContextMixin,
    CommentFormView,
    DelegatedViewMixin,
)
from hypha.apply.determinations.views import (
    BatchDeterminationCreateView,
    DeterminationCreateOrUpdateView,
)
from hypha.apply.projects.forms import CreateProjectForm
from hypha.apply.projects.models import Project
from hypha.apply.review.models import Review
from hypha.apply.review.views import ReviewContextMixin
from hypha.apply.stream_forms.blocks import GroupToggleBlock
from hypha.apply.users.decorators import staff_required
from hypha.apply.utils.models import PDFPageSettings
from hypha.apply.utils.pdfs import draw_submission_content, make_pdf
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import (
    DelegateableListView,
    DelegateableView,
    ViewDispatcher,
)

from .differ import compare
from .files import generate_submission_file_path
from .forms import (
    BatchDeleteSubmissionForm,
    BatchProgressSubmissionForm,
    BatchUpdateReviewersForm,
    BatchUpdateSubmissionLeadForm,
    CreateReminderForm,
    ProgressSubmissionForm,
    ScreeningSubmissionForm,
    UpdateMetaTermsForm,
    UpdatePartnersForm,
    UpdateReviewersForm,
    UpdateSubmissionLeadForm,
)
from .models import (
    ApplicationRevision,
    ApplicationSubmission,
    AssignedReviewers,
    LabBase,
    Reminder,
    ReviewerRole,
    ReviewerSettings,
    RoundBase,
    RoundsAndLabs,
)
from .permissions import is_user_has_access_to_view_submission
from .tables import (
    AdminSubmissionsTable,
    ReviewerLeaderboardDetailTable,
    ReviewerLeaderboardFilter,
    ReviewerLeaderboardTable,
    ReviewerSubmissionsTable,
    RoundsFilter,
    RoundsTable,
    StaffAssignmentsTable,
    SubmissionFilterAndSearch,
    SubmissionReviewerFilterAndSearch,
    SummarySubmissionsTable,
)
from .utils import get_default_screening_statues
from .workflow import (
    DRAFT_STATE,
    INITIAL_STATE,
    PHASES_MAPPING,
    STAGE_CHANGE_ACTIONS,
    active_statuses,
    review_statuses,
)

User = get_user_model()


class SubmissionStatsMixin:
    def get_context_data(self, **kwargs):
        submissions = ApplicationSubmission.objects.all()
        submission_undetermined_count = submissions.undetermined().count()
        review_my_count = submissions.reviewed_by(self.request.user).count()

        submission_value = submissions.current().value()
        submission_sum = intcomma(submission_value.get('value__sum'))
        submission_count = submission_value.get('value__count')

        submission_accepted = submissions.current_accepted()
        submission_accepted_value = submission_accepted.value()
        submission_accepted_sum = intcomma(submission_accepted_value.get('value__sum'))
        submission_accepted_count = submission_accepted.count()

        reviews = Review.objects.all()
        review_count = reviews.count()
        review_my_score = reviews.by_user(self.request.user).score()

        return super().get_context_data(
            submission_undetermined_count=submission_undetermined_count,
            review_my_count=review_my_count,
            submission_sum=submission_sum,
            submission_count=submission_count,
            submission_accepted_count=submission_accepted_count,
            submission_accepted_sum=submission_accepted_sum,
            review_count=review_count,
            review_my_score=review_my_score,
            **kwargs,
        )


class UpdateReviewersMixin:
    def set_status_after_reviewers_assigned(self, submission):
        # Check if all internal reviewers have been selected.
        if submission.has_all_reviewer_roles_assigned:
            # Automatic workflow actions.
            action = None
            if submission.status == INITIAL_STATE:
                # Automatically transition the application to "Internal review".
                action = submission.workflow.stepped_phases[2][0].name
            elif submission.status == 'proposal_discussion':
                # Automatically transition the proposal to "Internal review".
                action = 'proposal_internal_review'

            # If action is set run perform_transition().
            if action:
                try:
                    submission.perform_transition(
                        action,
                        self.request.user,
                        request=self.request,
                        notify=False,
                    )
                except (PermissionDenied, KeyError):
                    pass


class BaseAdminSubmissionsTable(SingleTableMixin, FilterView):
    table_class = AdminSubmissionsTable
    filterset_class = SubmissionFilterAndSearch
    filter_action = ''
    paginator_class = LazyPaginator
    table_pagination = {'per_page': 25}

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
        return self.filterset_class._meta.model.objects.exclude_draft().current().for_table(self.request.user)

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
class BatchUpdateReviewersView(UpdateReviewersMixin, DelegatedViewMixin, FormView):
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

        for submission in submissions:
            # Update submission status if needed.
            self.set_status_after_reviewers_assigned(submission)

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, mark_safe(_('Sorry something went wrong') + form.errors.as_ul()))
        return super().form_invalid(form)


@method_decorator(staff_required, name='dispatch')
class BatchDeleteSubmissionView(DelegatedViewMixin, FormView):
    form_class = BatchDeleteSubmissionForm
    context_name = 'batch_delete_submission_form'

    def form_valid(self, form):
        submissions = form.cleaned_data['submissions']
        messenger(
            MESSAGES.BATCH_DELETE_SUBMISSION,
            request=self.request,
            user=self.request.user,
            sources=submissions,
        )
        form.save()
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
        '''
        If use_settings variable is set for ReviewerSettings use settings
        parameters to filter submissions or return only reviewed_by as it
        was by default.
        '''
        reviewer_settings = ReviewerSettings.for_request(self.request)
        if reviewer_settings.use_settings:
            return super().get_queryset().for_reviewer_settings(
                self.request.user, reviewer_settings
            ).order_by('-submit_time')
        return super().get_queryset().reviewed_by(self.request.user)


@method_decorator(staff_required, name='dispatch')
class SubmissionOverviewView(BaseAdminSubmissionsTable):
    template_name = 'funds/submissions_overview.html'
    table_class = SummarySubmissionsTable
    table_pagination = False
    filter_action = reverse_lazy('funds:submissions:list')

    def get_table_data(self):
        limit = 5
        return super().get_table_data().order_by(F('last_update').desc(nulls_last=True))[:limit]

    def get_context_data(self, **kwargs):
        limit = 6
        base_query = RoundsAndLabs.objects.with_progress().active().order_by('-end_date')
        open_rounds = base_query.open()[:limit]
        open_query = '?round_state=open'
        closed_rounds = base_query.closed()[:limit]
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

        staff_flagged = self.get_staff_flagged()

        return super().get_context_data(
            open_rounds=open_rounds,
            open_query=open_query,
            closed_rounds=closed_rounds,
            closed_query=closed_query,
            rounds_title=rounds_title,
            status_counts=grouped_statuses,
            staff_flagged=staff_flagged,
            **kwargs,
        )

    def get_staff_flagged(self):
        qs = super().get_queryset().flagged_staff().order_by('-submit_time')
        row_attrs = dict({'data-flag-type': 'staff'}, **SummarySubmissionsTable._meta.row_attrs)

        limit = 5
        return {
            'table': SummarySubmissionsTable(qs[:limit], prefix='staff-flagged-', attrs={'class': 'all-submissions-table flagged-table'}, row_attrs=row_attrs),
            'display_more': qs.count() > limit,
        }


class SubmissionAdminListView(BaseAdminSubmissionsTable, DelegateableListView):
    template_name = 'funds/submissions.html'
    form_views = [
        BatchUpdateLeadView,
        BatchUpdateReviewersView,
        BatchProgressSubmissionView,
        BatchDeleteSubmissionView,
    ]


@method_decorator(staff_required, name='dispatch')
class GroupingApplicationsListView(TemplateView):
    '''
    Template view for grouped submissions
    '''
    template_name = 'funds/grouped_application_list.html'


class SubmissionReviewerListView(BaseReviewerSubmissionsTable):
    template_name = 'funds/submissions.html'


class SubmissionListView(ViewDispatcher):
    admin_view = SubmissionAdminListView
    reviewer_view = SubmissionReviewerListView


@method_decorator(staff_required, name='dispatch')
class SubmissionStaffFlaggedView(BaseAdminSubmissionsTable):
    template_name = 'funds/submissions_staff_flagged.html'

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current().for_table(self.request.user).flagged_staff().order_by('-submit_time')


@method_decorator(login_required, name='dispatch')
class SubmissionUserFlaggedView(UserPassesTestMixin, BaseAdminSubmissionsTable):
    template_name = 'funds/submissions_user_flagged.html'

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current().for_table(self.request.user).flagged_by(self.request.user).order_by('-submit_time')

    def test_func(self):
        return self.request.user.is_apply_staff or self.request.user.is_reviewer


@method_decorator(staff_required, name='dispatch')
class SubmissionsByRound(BaseAdminSubmissionsTable, DelegateableListView):
    template_name = 'funds/submissions_by_round.html'
    form_views = [
        BatchUpdateLeadView,
        BatchUpdateReviewersView,
        BatchProgressSubmissionView,
        BatchDeleteSubmissionView,
    ]

    excluded_fields = ('round', 'fund')

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
        BatchDeleteSubmissionView,
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
            related=', '.join([s.title for s in old.screening_statuses.all()]),
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
class UpdateReviewersView(UpdateReviewersMixin, DelegatedViewMixin, UpdateView):
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

        # Update submission status if needed.
        self.set_status_after_reviewers_assigned(form.instance)

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


@method_decorator(staff_required, name='dispatch')
class ReminderCreateView(DelegatedViewMixin, CreateView):
    context_name = 'reminder_form'
    form_class = CreateReminderForm
    model = Reminder

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.CREATE_REMINDER,
            request=self.request,
            user=self.request.user,
            source=self.object.submission,
            related=self.object,
        )

        return response


@method_decorator(staff_required, name='dispatch')
class ReminderDeleteView(DeleteView):
    model = Reminder

    def get_success_url(self):
        submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        return reverse_lazy('funds:submissions:detail', args=(submission.id,))

    def delete(self, request, *args, **kwargs):
        reminder = self.get_object()
        messenger(
            MESSAGES.DELETE_REMINDER,
            user=request.user,
            request=request,
            source=reminder.submission,
            related=reminder,
        )
        response = super().delete(request, *args, **kwargs)
        return response


class AdminSubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_admin_detail'
    model = ApplicationSubmission
    form_views = [
        ProgressSubmissionView,
        ScreeningSubmissionView,
        ReminderCreateView,
        CommentFormView,
        UpdateLeadView,
        UpdateReviewersView,
        UpdatePartnersView,
        CreateProjectView,
        UpdateMetaTermsView,
    ]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        if submission.status == DRAFT_STATE and not request.user == submission.user:
            raise Http404
        redirect = SubmissionSealedView.should_redirect(request, submission)
        return redirect or super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        other_submissions = self.model.objects.filter(user=self.object.user).current().exclude(id=self.object.id)
        if self.object.next:
            other_submissions = other_submissions.exclude(id=self.object.next.id)

        public_page = self.object.get_from_parent('detail')()
        default_screening_statuses = get_default_screening_statues()
        return super().get_context_data(
            other_submissions=other_submissions,
            public_page=public_page,
            default_screening_statuses=default_screening_statuses,
            **kwargs,
        )


class ReviewerSubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_reviewer_detail'
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers may sometimes be applicants as well.
        if submission.user == request.user:
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        if submission.status == DRAFT_STATE:
            raise Http404

        reviewer_settings = ReviewerSettings.for_request(request)
        if reviewer_settings.use_settings:
            queryset = ApplicationSubmission.objects.for_reviewer_settings(
                request.user, reviewer_settings
            )
            # Reviewer can't view submission which is not listed in ReviewerSubmissionsTable
            if not queryset.filter(id=submission.id).exists():
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class PartnerSubmissionDetailView(ActivityContextMixin, DelegateableView, DetailView):
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def get_object(self):
        return super().get_object().from_draft()

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Partners may sometimes be applicants as well.
        if submission.user == request.user:
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        # Only allow partners in the submission they are added as partners
        partner_has_access = submission.partners.filter(pk=request.user.pk).exists()
        if not partner_has_access:
            raise PermissionDenied
        if submission.status == DRAFT_STATE:
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class CommunitySubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView, DetailView):
    template_name_suffix = '_community_detail'
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Reviewers may sometimes be applicants as well.
        if submission.user == request.user:
            return ApplicantSubmissionDetailView.as_view()(request, *args, **kwargs)
        # Only allow community reviewers in submission with a community review state.
        if not submission.community_review:
            raise PermissionDenied
        if submission.status == DRAFT_STATE:
            raise Http404
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
        yield ('submit', 'primary', _('Submit'))
        yield ('save', 'white', _('Save draft'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.pop('instance').from_draft()
        initial = instance.raw_data
        for field_id in instance.file_field_ids:
            initial.pop(field_id + '-uploads', False)
            initial[field_id] = self.get_placeholder_file(
                instance.raw_data.get(field_id)
            )
        kwargs['initial'] = initial
        return kwargs

    def get_placeholder_file(self, initial_file):
        if not isinstance(initial_file, list):
            return PlaceholderUploadedFile(
                initial_file.filename, size=initial_file.size, file_id=initial_file.name
            )
        return [
            PlaceholderUploadedFile(f.filename, size=f.size, file_id=f.name)
            for f in initial_file
        ]

    def get_context_data(self, **kwargs):
        return super().get_context_data(buttons=self.buttons(), **kwargs)

    def get_form_class(self):
        draft = self.request.POST.get('save', False)
        form_fields = self.object.get_form_fields(draft, self.object.raw_data)
        field_blocks = self.object.get_defined_fields()
        for field_block in field_blocks:
            if isinstance(field_block.block, GroupToggleBlock):
                # Disable group toggle field as it is not supported on edit forms.
                form_fields[field_block.id].disabled = True
        return type('WagtailStreamForm', (self.object.submission_form_class,), form_fields)


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

        # Required for django-file-form: delete temporary files for the new files
        # uploaded while edit.
        form.delete_temporary_files()
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
        elif revision and not self.object.status == DRAFT_STATE:
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
                notify=not (revision or submitting_proposal) or self.object.status == DRAFT_STATE,  # Use the other notification
            )

        # Required for django-file-form: delete temporary files for the new files
        # uploaded while edit.
        form.delete_temporary_files()
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class PartnerSubmissionEditView(ApplicantSubmissionEditView):
    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        # If the requesting user submitted the application, return the Applicant view.
        # Partners may somtimes be applicants as well.
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


@method_decorator(staff_required, name='dispatch')
class SubmissionDetailPDFView(SingleObjectMixin, View):
    model = ApplicationSubmission

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)

        if not hasattr(obj, 'project'):
            raise Http404

        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        pdf_page_settings = PDFPageSettings.for_request(request)
        content = draw_submission_content(
            self.object.output_text_answers()
        )
        pdf = make_pdf(
            title=self.object.title,
            sections=[
                {
                    'content': content,
                    'title': 'Submission',
                    'meta': [
                        self.object.stage,
                        self.object.page,
                        self.object.round,
                        f"Lead: { self.object.lead }",
                    ],
                },
            ],
            pagesize=pdf_page_settings.download_page_size,
        )
        return FileResponse(
            pdf,
            as_attachment=True,
            filename=self.object.title + '.pdf',
        )


@method_decorator(cache_page(60), name='dispatch')
@method_decorator(staff_required, name='dispatch')
class SubmissionResultView(SubmissionStatsMixin, FilterView):
    template_name = 'funds/submissions_result.html'
    filterset_class = SubmissionFilterAndSearch
    filter_action = ''

    excluded_fields = []

    @property
    def excluded(self):
        return {
            'exclude': self.excluded_fields
        }

    def get_filterset_kwargs(self, filterset_class, **kwargs):
        new_kwargs = super().get_filterset_kwargs(filterset_class)
        new_kwargs.update(self.excluded)
        new_kwargs.update(kwargs)
        return new_kwargs

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current()

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')
        submission_values = self.object_list.value()
        count_values = submission_values.get('value__count')
        total_value = intcomma(submission_values.get('value__sum'))
        average_value = intcomma(round(submission_values.get('value__avg')))

        return super().get_context_data(
            search_term=search_term,
            filter_action=self.filter_action,
            count_values=count_values,
            total_value=total_value,
            average_value=average_value,
            **kwargs,
        )


@method_decorator(staff_required, name='dispatch')
class ReviewerLeaderboard(SingleTableMixin, FilterView):
    filterset_class = ReviewerLeaderboardFilter
    filter_action = ''
    table_class = ReviewerLeaderboardTable
    table_pagination = False
    template_name = 'funds/reviewer_leaderboard.html'

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')

        return super().get_context_data(
            search_term=search_term,
            filter_action=self.filter_action,
            **kwargs,
        )

    def get_queryset(self):
        # Only list reviewers.
        return self.filterset_class._meta.model.objects.reviewers()

    def get_table_data(self):
        ninety_days_ago = timezone.now() - timedelta(days=90)
        this_year = timezone.now().year
        last_year = timezone.now().year - 1
        return super().get_table_data().annotate(
            total=Count('assignedreviewers__review'),
            ninety_days=Count('assignedreviewers__review', filter=Q(assignedreviewers__review__created_at__date__gte=ninety_days_ago)),
            this_year=Count('assignedreviewers__review', filter=Q(assignedreviewers__review__created_at__year=this_year)),
            last_year=Count('assignedreviewers__review', filter=Q(assignedreviewers__review__created_at__year=last_year)),
        )


@method_decorator(staff_required, name='dispatch')
class ReviewerLeaderboardDetail(SingleTableMixin, ListView):
    model = Review
    table_class = ReviewerLeaderboardDetailTable
    paginator_class = LazyPaginator
    table_pagination = {'per_page': 25}
    template_name = 'funds/reviewer_leaderboard_detail.html'

    def get_context_data(self, **kwargs):
        obj = User.objects.get(pk=self.kwargs.get('pk'))
        return super().get_context_data(object=obj, **kwargs)

    def get_table_data(self):
        return super().get_table_data().filter(author__reviewer_id=self.kwargs.get('pk')).select_related('submission')


class RoleColumn(tables.Column):
    def render(self, value, record):
        return AssignedReviewers.objects.filter(
            reviewer=record, role=self.verbose_name, submission__status__in=active_statuses
        ).count()


@method_decorator(staff_required, name='dispatch')
class StaffAssignments(SingleTableMixin, ListView):
    model = User
    table_class = StaffAssignmentsTable
    table_pagination = False
    template_name = 'funds/staff_assignments.html'

    def get_queryset(self):
        # Only list staff.
        return self.model.objects.staff()

    def get_table_data(self):
        table_data = super().get_table_data()
        reviewer_roles = ReviewerRole.objects.all().order_by('order')
        for data in table_data:
            for i, role in enumerate(reviewer_roles):
                # Only setting column name with dummy value 0.
                # Actual value will be set in RoleColumn render method.
                setattr(data, f'role{i}', 0)
        return table_data

    def get_table_kwargs(self):
        reviewer_roles = ReviewerRole.objects.all().order_by('order')
        extra_columns = []
        for i, role in enumerate(reviewer_roles):
            extra_columns.append((f'role{i}', RoleColumn(verbose_name=role)))
        return {
            'extra_columns': extra_columns,
        }
