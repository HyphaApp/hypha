from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from opentech.apply.activity.views import (
    AllActivityContextMixin,
    ActivityContextMixin,
    CommentFormView,
    DelegatedViewMixin,
)
from opentech.apply.activity.models import Activity
from opentech.apply.review.views import ReviewContextMixin
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import DelegateableView, ViewDispatcher

from .blocks import MustIncludeFieldBlock
from .forms import ProgressSubmissionForm, UpdateReviewersForm, UpdateSubmissionLeadForm
from .models import ApplicationSubmission
from .tables import AdminSubmissionsTable, SubmissionFilter, SubmissionFilterAndSearch
from .workflow import SingleStage, DoubleStage


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
        old_phase = form.instance.phase.display_name
        response = super().form_valid(form)
        new_phase = form.instance.phase.display_name
        Activity.actions.create(
            user=self.request.user,
            submission=self.kwargs['submission'],
            message=f'Progressed from {old_phase} to {new_phase}'
        )
        return response


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
        if not self.get_object().phase.has_perm(request.user, 'edit'):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        instance = kwargs.pop('instance')
        form_data = instance.form_data

        for field in self.object.form_fields:
            if isinstance(field.block, MustIncludeFieldBlock):
                # convert certain data to the correct field id
                try:
                    response = form_data[field.block.name]
                except KeyError:
                    pass
                else:
                    form_data[field.id] = response

        kwargs['initial'] = form_data
        return kwargs

    def get_form_class(self):
        return self.object.get_form_class()

    def form_valid(self, form):
        self.object.form_data = form.cleaned_data
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


workflows = [SingleStage, DoubleStage]


# Workflow Demo Views

class BasicSubmissionForm(forms.Form):
    who_are_you = forms.CharField()


def demo_workflow(request, wf_id):
    logs = request.session.get('logs', list())
    submission = request.session.get('submission', dict())

    wf = int(wf_id)
    workflow_class = workflows[wf - 1]
    workflow = workflow_class()
    forms = [BasicSubmissionForm] * wf

    current_phase = request.POST.get('current')
    current = workflow.current(current_phase)

    if request.POST:
        if current.stage.name not in submission:
            form = forms[workflow.stages.index(current.stage)]
            submitted_form = form(request.POST)
            if submitted_form.is_valid():
                submission[current.stage.name] = submitted_form.cleaned_data
                phase = current
                logs.append(
                    f'{phase.stage}: Form was submitted'
                )
                form = None
            else:
                form = submitted_form
        else:
            phase = workflow.process(current_phase, request.POST['action'])
            logs.append(
                f'{current.stage}: {current.name} was updated to {phase.stage}: {phase.name}'
            )
    else:
        phase = current
        logs.clear()
        submission.clear()

    if phase.stage.name not in submission:
        form = forms[workflow.stages.index(phase.stage)]
    else:
        form = None

    request.session['logs'] = logs
    request.session['submission'] = submission

    context = {
        'workflow': workflow,
        'phase': phase,
        'logs': logs,
        'data': submission,
        'form': form,
    }
    return TemplateResponse(request, 'funds/demo_workflow.html', context)
