from copy import copy

from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView, FormView, UpdateView

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.activity.views import ActivityContextMixin, CommentFormView
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import (DelegateableView, DelegatedViewMixin,
                                        ViewDispatcher)

from .forms import (CreateApprovalForm, ProjectEditForm, RejectionForm,
                    SetPendingForm, UpdateProjectLeadForm)
from .models import CONTRACTING, Approval, DocumentCategory, Project


@method_decorator(staff_required, name='dispatch')
class CreateApprovalView(DelegatedViewMixin, CreateView):
    context_name = 'add_approval_form'
    form_class = CreateApprovalForm
    model = Approval

    @transaction.atomic()
    def form_valid(self, form):
        try:
            project = Project.objects.get(pk=self.kwargs['pk'])
        except Project.DoesNotExist:
            raise Http404("No Project found with ID={self.kwargs['pk']}")

        Approval.objects.create(
            by=self.request.user,
            project=project,
        )

        project.is_locked = False
        project.status = CONTRACTING
        project.save(update_fields=['is_locked', 'status'])

        messenger(
            MESSAGES.APPROVE_PROJECT,
            request=self.request,
            user=self.request.user,
            source=project,
        )

        return redirect(project)


@method_decorator(staff_required, name='dispatch')
class RejectionView(DelegatedViewMixin, FormView):
    context_name = 'rejection_form'
    form_class = RejectionForm
    model = Project

    def form_valid(self, form):
        try:
            project = Project.objects.get(pk=self.kwargs['pk'])
        except Project.DoesNotExist:
            raise Http404("No Project found with ID={self.kwargs['pk']}")

        messenger(
            MESSAGES.REJECT_PROJECT,
            request=self.request,
            user=self.request.user,
            source=project,
            comment=form.cleaned_data['comment'],
        )
        return redirect(project)


@method_decorator(staff_required, name='dispatch')
class SendForApprovalView(DelegatedViewMixin, UpdateView):
    context_name = 'request_approval_form'
    form_class = SetPendingForm
    model = Project

    def form_valid(self, form):
        # lock project
        response = super().form_valid(form)

        messenger(
            MESSAGES.SEND_FOR_APPROVAL,
            request=self.request,
            user=self.request.user,
            source=form.instance.submission,
            project=form.instance,
        )

        return response


@method_decorator(staff_required, name='dispatch')
class UpdateLeadView(DelegatedViewMixin, UpdateView):
    model = Project
    form_class = UpdateProjectLeadForm
    context_name = 'lead_form'

    def form_valid(self, form):
        # Fetch the old lead from the database
        old = copy(self.get_object())

        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_PROJECT_LEAD,
            request=self.request,
            user=self.request.user,
            source=form.instance,
            related=old.lead or 'Unassigned',
        )

        return response


class AdminProjectDetailView(ActivityContextMixin, DelegateableView, DetailView):
    form_views = [
        CommentFormView,
        CreateApprovalView,
        RejectionView,
        SendForApprovalView,
        UpdateLeadView,
    ]
    model = Project
    template_name_suffix = '_admin_detail'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            remaining_document_categories=DocumentCategory.objects.all(),
            **kwargs,
        )


class ApplicantProjectDetailView(DetailView):
    model = Project


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView


@method_decorator(staff_required, name='dispatch')
class ProjectEditView(UpdateView):
    form_class = ProjectEditForm
    model = Project
