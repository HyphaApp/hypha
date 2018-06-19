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
from .models import Determination, UNDETERMINED


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
        return self.model.objects.get(submission=self.submission, author=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])

        if self.submission.phase not in DETERMINATION_PHASES \
                and not self.submission.user_lead_or_admin(request.user):
            raise PermissionDenied()

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        try:
            has_determination_response = self.submission.determination.determination != UNDETERMINED \
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
            kwargs['initial'] = self.object.determination_data
            kwargs['initial']['determination'] = self.object.determination
            kwargs['initial']['determination_message'] = self.object.determination_message

        return kwargs

    def get_success_url(self):
        return self.submission.get_absolute_url()


@method_decorator(login_required, name='dispatch')
class DeterminationDetailView(DetailView):
    model = Determination

    def dispatch(self, request, *args, **kwargs):
        determination = self.get_object()
        submission = determination.submission

        if request.user != submission.user and request.user != submission.lead \
                and not request.user.is_apply_staff and not request.user.is_superuser:
            raise PermissionDenied

        if determination.is_draft:
            return HttpResponseRedirect(reverse_lazy('apply:submissions:determinations:form', args=(submission.id,)))

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        determination_data = self.get_object().determination_data
        form_used = get_form_for_stage(self.get_object().submission)
        form_determination_data = {}

        for name, field in form_used.base_fields.items():
            try:
                # Add any titles that exist
                title = form_used.titles[field.group]
                form_determination_data.setdefault(title, '')
            except AttributeError:
                pass

            try:
                value = determination_data[name]
                form_determination_data.setdefault(field.label, str(value))
            except KeyError:
                pass

        lead_or_admin = self.request.user.is_superuser or self.request.user == self.get_object().submission.lead

        return super().get_context_data(
            can_view_extended_data=lead_or_admin,
            determination_data=form_determination_data,
            **kwargs
        )
