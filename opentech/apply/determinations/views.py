from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView
from django_fsm import can_proceed

from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.utils.views import CreateOrUpdateView

from .forms import ConceptDeterminationForm, ProposalDeterminationForm
from .models import Determination, DETERMINATION_TRANSITION_SUFFIX, DeterminationMessageSettings


def get_form_for_stage(submission):
    forms = [ConceptDeterminationForm, ProposalDeterminationForm]
    index = submission.workflow.stages.index(submission.stage)
    return forms[index]


class DeterminationCreateOrUpdateView(CreateOrUpdateView):
    model = Determination
    template_name = 'determinations/determination_form.html'

    def get_object(self, queryset=None):
        return self.model.objects.get(submission=self.submission)

    def dispatch(self, request, *args, **kwargs):
        self.submission = get_object_or_404(ApplicationSubmission, id=self.kwargs['submission_pk'])

        if not self.submission.in_determination_phase \
                or not self.submission.has_permission_to_add_determination(request.user):
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
            has_determination_response = self.submission.determination.submitted
        except ObjectDoesNotExist:
            has_determination_response = False

        messages = DeterminationMessageSettings.for_site(self.request.site)

        return super().get_context_data(
            submission=self.submission,
            has_determination_response=has_determination_response,
            title="Update Determination draft" if self.object else 'Add Determination',
            message_templates=messages.get_for_stage(self.submission.stage.name),
            **kwargs
        )

    def get_form_class(self):
        return get_form_for_stage(self.submission)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['submission'] = self.submission
        kwargs['action'] = self.request.GET.get('action')
        return kwargs

    def get_success_url(self):
        return self.submission.get_absolute_url()

    def form_valid(self, form):
        response = super().form_valid(form)

        if not self.object.is_draft:
            action_name = self.get_action_name_from_determination(int(form.cleaned_data.get('outcome')))
            self.submission.perform_transition(action_name, self.request.user)

        return self.progress_stage(self.submission) or response

    def progress_stage(self, instance):
        proposal_transition = instance.get_transition('draft_proposal')
        if proposal_transition:
            if can_proceed(proposal_transition):
                proposal_transition(by=self.request.user)
                instance.save()
            return HttpResponseRedirect(instance.get_absolute_url())

    def form_invalid(self, form):
        from pprint import pprint
        pprint(form.errors)
        return super().form_invalid(form)

    def get_action_name_from_determination(self, determination):
        suffix = DETERMINATION_TRANSITION_SUFFIX[determination]

        for transition_name in self.submission.phase.transitions:
            if type(suffix) is list:
                for item in suffix:
                    if item in transition_name:
                        return transition_name
            else:
                if suffix in transition_name:
                    return transition_name


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
                form_data.setdefault(title, '<field_group_title>')
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
