from copy import copy

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.text import mark_safe
from django.views.generic import DetailView, ListView, UpdateView

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from opentech.apply.activity.views import (
    AllActivityContextMixin,
    ActivityContextMixin,
    CommentFormView,
    DelegatedViewMixin,
)
from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.funds.workflow import DETERMINATION_OUTCOMES
from opentech.apply.review.views import ReviewContextMixin
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import DelegateableView, ViewDispatcher

from .differ import compare
from .forms import ProgressSubmissionForm, UpdateReviewersForm, UpdateSubmissionLeadForm
from .models import ApplicationSubmission, ApplicationRevision
from .tables import AdminSubmissionsTable, SubmissionFilter, SubmissionFilterAndSearch


@method_decorator(staff_required, name='dispatch')
class SubmissionListView(AllActivityContextMixin, SingleTableMixin, FilterView):
    template_name = 'funds/submissions.html'
    table_class = AdminSubmissionsTable

    filterset_class = SubmissionFilter

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current()

    def get_context_data(self, **kwargs):
        active_filters = self.filterset.data
        return super().get_context_data(active_filters=active_filters, **kwargs)


@method_decorator(staff_required, name='dispatch')
class SubmissionSearchView(SingleTableMixin, FilterView):
    template_name = 'funds/submissions_search.html'
    table_class = AdminSubmissionsTable

    filterset_class = SubmissionFilterAndSearch

    def get_queryset(self):
        return self.filterset_class._meta.model.objects.current()

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')

        # We have more data than just 'query'
        active_filters = len(self.filterset.data) > 1

        return super().get_context_data(
            search_term=search_term,
            active_filters=active_filters,
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
        if action in DETERMINATION_OUTCOMES and not self.object.has_determination:
            return HttpResponseRedirect(reverse_lazy(
                'apply:submissions:determinations:form',
                args=(form.instance.id,)) + "?action=" + action)

        self.object.perform_transition(action, self.request.user, request=self.request)

        if self.object.phase.name == 'proposal_discussion' and action == 'proposal_discussion':
            messenger(
                MESSAGES.PROPOSAL_SUBMITTED,
                request=self.request,
                user=self.request.user,
                submission=self.object.instance,
            )

        return super().form_valid(form)


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
            submission=form.instance,
            old=old,
        )
        return response


@method_decorator(staff_required, name='dispatch')
class UpdateReviewersView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = UpdateReviewersForm
    context_name = 'reviewer_form'

    def form_valid(self, form):
        old_reviewers = set(self.get_object().reviewers.all())
        response = super().form_valid(form)
        new_reviewers = set(form.instance.reviewers.all())

        added = new_reviewers - old_reviewers
        removed = old_reviewers - new_reviewers

        messenger(
            MESSAGES.REVIEWERS_UPDATED,
            request=self.request,
            user=self.request.user,
            submission=self.kwargs['submission'],
            added=added,
            removed=removed,
        )
        return response


class AdminSubmissionDetailView(ReviewContextMixin, ActivityContextMixin, DelegateableView):
    template_name_suffix = '_admin_detail'
    model = ApplicationSubmission
    form_views = [
        ProgressSubmissionView,
        CommentFormView,
        UpdateLeadView,
        UpdateReviewersView,
    ]

    def dispatch(self, request, *args, **kwargs):
        submission = self.get_object()
        redirect = SubmissionSealedView.should_redirect(request, submission)
        return redirect or super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        other_submissions = self.model.objects.filter(user=self.object.user).current().exclude(id=self.object.id)
        if self.object.next:
            other_submissions = other_submissions.exclude(id=self.object.next.id)

        return super().get_context_data(
            other_submissions=other_submissions,
            **kwargs,
        )


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
            submission=submission,
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


class ApplicantSubmissionDetailView(ActivityContextMixin, DelegateableView):
    model = ApplicationSubmission
    form_views = [CommentFormView]

    def get_object(self):
        return super().get_object().from_draft()

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SubmissionDetailView(ViewDispatcher):
    admin_view = AdminSubmissionDetailView
    applicant_view = ApplicantSubmissionDetailView

    def admin_check(self, request):
        if request.user.is_reviewer:
            return True
        return super().admin_check(request)


@method_decorator(login_required, name='dispatch')
class SubmissionEditView(UpdateView):
    """
    Converts the data held on the submission into an editable format and knows how to save
    that back to the object. Shortcuts the normal update view save approach
    """
    model = ApplicationSubmission

    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object().user:
            raise PermissionDenied
        if not self.get_object().phase.permissions.can_edit(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    @property
    def transitions(self):
        transitions = self.object.get_available_user_status_transitions(self.request.user)
        return {
            transition.name: transition
            for transition in transitions
        }

    def buttons(self):
        yield ('save', 'Save')
        yield from ((transition, transition.title) for transition in self.transitions)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.pop('instance').from_draft()
        kwargs['initial'] = instance.raw_data
        return kwargs

    def get_context_data(self, **kwargs):
        return super().get_context_data(buttons=self.buttons(), **kwargs)

    def get_form_class(self):
        return self.object.get_form_class()

    def form_valid(self, form):
        self.object.new_data(form.cleaned_data)

        if 'save' in self.request.POST:
            self.object.create_revision(draft=True, by=self.request.user)
            return self.form_invalid(form)

        action = set(self.request.POST.keys()) & set(self.transitions.keys())

        transition = self.transitions[action.pop()]
        self.object.perform_transition(transition.target, self.request.user, request=self.request)

        return HttpResponseRedirect(self.get_success_url())


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


class RevisionCompareView(DetailView):
    model = ApplicationSubmission
    template_name = 'funds/revisions_compare.html'
    pk_url_kwarg = 'submission_pk'

    def compare_revisions(self, from_data, to_data):
        diffed_form_data = {
            field: compare(from_data.form_data.get(field), to_data.form_data[field])
            for field in to_data.form_data
        }
        self.object.form_data = from_data.form_data
        from_fields = self.object.render_answers()

        self.object.form_data = to_data.form_data
        to_fields = self.object.render_answers()

        diffed_answers = [
            compare(*fields, should_bleach=False)
            for fields in zip(from_fields, to_fields)
        ]
        self.object.form_data = diffed_form_data
        self.object.output_answers = mark_safe(''.join(diffed_answers))

    def get_context_data(self, **kwargs):
        from_revision = self.object.revisions.get(id=self.kwargs['from'])
        to_revision = self.object.revisions.get(id=self.kwargs['to'])
        self.object = self.compare_revisions(from_revision, to_revision)
        return super().get_context_data(**kwargs)
