from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, TemplateView

from django_filters.views import FilterView
from django_fsm import can_proceed
from django_tables2.views import SingleTableMixin

from opentech.apply.activity.views import (
    AllActivityContextMixin,
    ActivityContextMixin,
    CommentFormView,
    DelegatedViewMixin,
)
from opentech.apply.activity.models import Activity
from opentech.apply.funds.workflow import DETERMINATION_RESPONSE_TRANSITIONS
from opentech.apply.review.views import ReviewContextMixin
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import DelegateableView, ViewDispatcher
from opentech.apply.users.models import User

from .blocks import MustIncludeFieldBlock
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
        if action in DETERMINATION_RESPONSE_TRANSITIONS:
            return HttpResponseRedirect(reverse_lazy(
                'apply:submissions:determinations:form',
                args=(form.instance.id,)) + "?action=" + action)

        form.instance.perform_transition(action, self.request.user)

        response = super().form_valid(form)
        return self.progress_stage(form.instance) or response

    def progress_stage(self, instance):
        try:
            instance.perform_transition('draft_proposal', self.request.user)
        except PermissionDenied:
            pass
        else:
            return HttpResponseRedirect(instance.get_absolute_url())


@method_decorator(staff_required, name='dispatch')
class UpdateLeadView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = UpdateSubmissionLeadForm
    context_name = 'lead_form'

    def form_valid(self, form):
        # Fetch the old lead from the database
        old_lead = self.get_object().lead
        response = super().form_valid(form)
        new_lead = form.instance.lead
        Activity.actions.create(
            user=self.request.user,
            submission=self.kwargs['submission'],
            message=f'Lead changed from {old_lead} to {new_lead}'
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

        message = ['Reviewers updated.']
        added = new_reviewers - old_reviewers
        if added:
            message.append('Added:')
            message.append(', '.join([str(user) for user in added]) + '.')

        removed = old_reviewers - new_reviewers
        if removed:
            message.append('Removed:')
            message.append(', '.join([str(user) for user in removed]) + '.')

        Activity.actions.create(
            user=self.request.user,
            submission=self.kwargs['submission'],
            message=' '.join(message),
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

    def get_context_data(self, **kwargs):
        other_submissions = self.model.objects.filter(user=self.object.user).current().exclude(id=self.object.id)
        if self.object.next:
            other_submissions = other_submissions.exclude(id=self.object.next.id)

        return super().get_context_data(
            other_submissions=other_submissions,
            **kwargs,
        )


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
        instance = kwargs.pop('instance')
        kwargs['initial'] = instance.raw_data
        return kwargs

    def get_context_data(self, **kwargs):
        return super().get_context_data(buttons=self.buttons(), **kwargs)

    def get_form_class(self):
        return self.object.get_form_class()

    def form_valid(self, form):
        self.object.form_data = form.cleaned_data

        if 'save' in self.request.POST:
            self.object.create_revision(draft=True)
            return self.form_invalid(form)

        action = set(self.request.POST.keys()) & set(self.transitions.keys())

        transition = self.transitions[action.pop()]
        self.object.perform_transition(transition.target, self.request.user)

        return HttpResponseRedirect(self.get_success_url())


@method_decorator(staff_required, name='dispatch')
class RevisionListView(ListView):
    model = Revision

    def dispatch(self):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        self.queryset = self.model.objects.filter(submission=self.submission)
        return super().get_queryset()


    def get_context_data(self, **kwargs):
        return super().get_context_data(
            submission=self.submission,
            **kwargs,
        )
