from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView

from opentech.apply.activity.models import Activity
from opentech.apply.activity.messaging import messenger, MESSAGES
from opentech.apply.funds.models import ApplicationSubmission
from opentech.apply.utils.views import CreateOrUpdateView

from .forms import ConceptDeterminationForm, ProposalDeterminationForm
from .models import Determination, TRANSITION_DETERMINATION, DeterminationMessageSettings, NEEDS_MORE_INFO


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
        messages = DeterminationMessageSettings.for_site(self.request.site)

        return super().get_context_data(
            submission=self.submission,
            has_determination_response=self.submission.has_determination,
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
            messenger(
                MESSAGES.DETERMINATION_OUTCOME,
                request=self.request,
                user=self.object.author,
                submission=self.object.submission,
            )
            transition = self.transition_from_outcome(int(form.cleaned_data.get('outcome')))

            if self.object.outcome == NEEDS_MORE_INFO:
                # We keep a record of the message sent to the user in the comment
                Activity.comments.create(
                    message=self.object.clean_message,
                    user=self.request.user,
                    submission=self.submission,
                )

            self.submission.perform_transition(transition, self.request.user, request=self.request)

        return self.progress_stage(self.submission) or response

    def progress_stage(self, instance):
        try:
            instance.perform_transition('draft_proposal', self.request.user, request=self.request)
        except PermissionDenied:
            pass
        else:
            messenger(
                MESSAGES.INVITED_TO_PROPOSAL,
                request=self.request,
                user=self.request.user,
                submission=instance,
            )
            return HttpResponseRedirect(instance.get_absolute_url())

    def transition_from_outcome(self, outcome):
        for transition_name in self.submission.phase.transitions:
            try:
                transition_type = TRANSITION_DETERMINATION[transition_name]
            except KeyError:
                pass
            else:
                if transition_type == outcome:
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

        return super().get_context_data(
            can_view_extended_data=determination.submission.has_permission_to_add_determination(self.request.user),
            determination_data=determination.detailed_data,
            **kwargs
        )
