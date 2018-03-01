from django import forms
from django.template.response import TemplateResponse
from django.views.generic import DetailView, UpdateView, View

from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin

from opentech.apply.activity.views import ActivityContextMixin, CommentFormView, DelegatedViewMixin
from opentech.apply.activity.models import Activity

from .forms import ProgressSubmissionForm
from .models import ApplicationSubmission
from .tables import SubmissionsTable, SubmissionFilter, SubmissionFilterAndSearch
from .workflow import SingleStage, DoubleStage


class SubmissionListView(SingleTableMixin, FilterView):
    template_name = 'funds/submissions.html'
    table_class = SubmissionsTable

    filterset_class = SubmissionFilter

    def get_context_data(self, **kwargs):
        active_filters = self.filterset.data
        return super().get_context_data(active_filters=active_filters, **kwargs)


class SubmissionSearchView(SingleTableMixin, FilterView):
    template_name = 'funds/submissions_search.html'
    table_class = SubmissionsTable

    filterset_class = SubmissionFilterAndSearch

    def get_context_data(self, **kwargs):
        search_term = self.request.GET.get('query')

        # We have more data than just 'query'
        active_filters = len(self.filterset.data) > 1

        return super().get_context_data(
            search_term=search_term,
            active_filters=active_filters,
            **kwargs,
        )


class ProgressContextMixin(View):
    def get_context_data(self, **kwargs):
        extra = {
            ProgressSubmissionView.context_name: ProgressSubmissionView.form_class(instance=self.object),
        }

        return super().get_context_data(**extra, **kwargs)


class ProgressSubmissionView(DelegatedViewMixin, UpdateView):
    model = ApplicationSubmission
    form_class = ProgressSubmissionForm
    context_name = 'progress_form'

    def form_valid(self, form):
        old_phase = form.instance.phase.name
        response = super().form_valid(form)
        new_phase = form.instance.phase.name
        Activity.activities.create(
            user=self.request.user,
            submission=self.kwargs['submission'],
            message=f'Progressed from {old_phase} to {new_phase}'
        )
        return response


class SubmissionDetailView(ActivityContextMixin, ProgressContextMixin, DetailView):
    model = ApplicationSubmission
    form_views = {
        'progress': ProgressSubmissionView,
        'comment': CommentFormView,
    }

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            other_submissions=self.model.objects.filter(user=self.object.user).exclude(id=self.object.id),
            **kwargs
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        kwargs['submission'] = self.object

        # Information to pretend we originate from this view
        kwargs['template_names'] = self.get_template_names()
        kwargs['context'] = self.get_context_data()

        form_submitted = request.POST['form-submitted'].lower()
        view = self.form_views[form_submitted].as_view()

        return view(request, *args, **kwargs)


workflows = [SingleStage, DoubleStage]


# Workflow Demo Views

class BasicSubmissionForm(forms.Form):
    who_are_you = forms.CharField()


def demo_workflow(request, wf_id):
    logs = request.session.get('logs', list())
    submission = request.session.get('submission', dict())

    wf = int(wf_id)
    workflow_class = workflows[wf - 1]
    workflow = workflow_class([BasicSubmissionForm] * wf)

    current_phase = request.POST.get('current')
    current = workflow.current(current_phase)

    if request.POST:
        if current.stage.name not in submission:
            submitted_form = current.stage.form(request.POST)
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
        form = phase.stage.form
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
