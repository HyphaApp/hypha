from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import ProcessFormView, ModelFormMixin

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.funds.workflow import DETERMINATION_PHASES

from .forms import ConceptDeterminationForm, ProposalDeterminationForm
from .models import Determination, NEEDS_MORE_INFO


def get_form_for_stage(submission):
    forms = [ConceptDeterminationForm, ProposalDeterminationForm]
    index = submission.workflow.stages.index(submission.stage)
    return forms[index]


class CreateOrUpdateView(SingleObjectTemplateResponseMixin, ModelFormMixin, ProcessFormView):

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            self.object = None

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except self.model.DoesNotExist:
            self.object = None

        return super().post(request, *args, **kwargs)


class DeterminationCreateOrUpdateView(CreateOrUpdateView):
    model = Determination
    template_name = 'determinations/determination_form.html'

    def get_object(self, queryset=None):
        return self.model.objects.get(submission=self.submission)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])

        if self.submission.phase not in DETERMINATION_PHASES \
                and not self.submission.has_permission_to_add_determination(request.user):
            raise PermissionDenied()

        try:
            submitted = self.get_object().submitted
        except Determination.DoesNotExist:
            submitted = False

        if self.request.POST and submitted:
            return self.get(request, *args, **kwargs)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        try:
            has_determination_response = self.submission.determination.outcome != NEEDS_MORE_INFO \
                                         and not self.submission.determination.is_draft
        except ObjectDoesNotExist:
            has_determination_response = False

        return super().get_context_data(
            submission=self.submission,
            has_determination_response=has_determination_response,
            title="Update Determination draft" if self.object else 'Add Determination',
            **kwargs
        )

    def get_form_class(self):
        return get_form_for_stage(self.submission)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        kwargs['submission'] = self.submission

        if self.object:
            kwargs['initial'] = self.object.data
            kwargs['initial']['outcome'] = self.object.outcome
            kwargs['initial']['message'] = self.object.message

        return kwargs

    def get_success_url(self):
        return self.submission.get_absolute_url()


@method_decorator(login_required, name='dispatch')
class DeterminationDetailView(DetailView):
    model = Determination

    def get_object(self, queryset=None):
        return self.model.objects.get(submission=self.submission)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])
        determination = self.get_object()

        if request.user != self.submission.user and not request.user.is_apply_staff and not \
                self.submission.has_permission_to_add_determination(request.user):
            raise PermissionDenied

        if determination.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:determinations:form', args=(self.submission.id,)))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        determination = self.get_object()
        form_used = get_form_for_stage(determination.submission)
        form_data = {}

        for name, field in form_used.base_fields.items():
            try:
                # Add any titles that exist
                title = form_used.titles[field.group]
                form_data.setdefault(title, '')
            except AttributeError:
                pass

            try:
                value = determination.data[name]
                form_data.setdefault(field.label, str(value))
            except KeyError:
                pass

        return super().get_context_data(
            can_view_extended_data=determination.submission.has_permission_to_add_determination(self.request.user),
            determination_data=form_data,
            **kwargs
        )
