from copy import copy

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, DetailView, FormView, UpdateView

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.activity.views import ActivityContextMixin, CommentFormView
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.views import (
    DelegateableView,
    DelegatedViewMixin,
    ViewDispatcher
)

from .forms import (
    ApproveContractForm,
    CreateApprovalForm,
    ProjectApprovalForm,
    ProjectEditForm,
    RejectionForm,
    RemoveDocumentForm,
    SetPendingForm,
    UpdateProjectLeadForm,
    UploadContractForm,
    UploadDocumentForm
)
from .models import (
    CONTRACTING,
    IN_PROGRESS,
    Approval,
    Contract,
    PacketFile,
    Project
)


class ContractsMixin:
    def get_context_data(self, **kwargs):
        project = self.get_object()
        contracts = self.get_contracts(project)

        try:
            latest_contract = contracts[0]
        except TypeError:
            latest_contract = None

        context = super().get_context_data(**kwargs)
        context['latest_contract'] = latest_contract
        context['contracts'] = contracts
        return context

    def get_contracts(self, project):
        """
        Get approved AND signed contracts for the current project

        When an unsigned OR (signed AND unapproved) contract is newer than the
        signed and approved ones we add that to the top of the list.
        """
        contracts = (project.contracts.select_related('approver')
                                      .order_by('-created_at'))

        if not contracts.exists():
            return

        latest_contract = contracts.first()

        if latest_contract.is_signed and latest_contract.approver:
            return contracts.filter(is_signed=True, approver__isnull=False)

        # At this point we know that latest_contract is the "pending" contract
        # we want to display at the top of the list, however we need to remove
        # all the older pending contracts from the list.
        #
        # We do that by getting the PKs for all the contracts which are (signed
        # AND approved), adding the latest_contract's PK and returning the
        # filter of those.
        ready_pks = list(contracts.filter(is_signed=True, approver__isnull=False)
                                  .values_list('pk', flat=True))

        return contracts.filter(pk__in=[latest_contract.pk, *ready_pks])


@method_decorator(staff_required, name='dispatch')
class ApproveContractView(UpdateView):
    form_class = ApproveContractForm
    model = Contract
    pk_url_kwarg = 'contract_pk'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        for error in form.errors:
            messages.error(self.request, error)

        return redirect(self.project)

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.approver = self.request.user
            form.instance.project = self.project
            response = super().form_valid(form)

            messenger(
                MESSAGES.APPROVE_CONTRACT,
                request=self.request,
                user=self.request.user,
                source=self.project,
                related=self.object,
            )

            self.project.status = IN_PROGRESS
            self.project.save(update_fields=['status'])

        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


@method_decorator(staff_required, name='dispatch')
class CreateApprovalView(DelegatedViewMixin, CreateView):
    context_name = 'add_approval_form'
    form_class = CreateApprovalForm
    model = Approval

    @transaction.atomic()
    def form_valid(self, form):
        project = self.kwargs['object']
        form.instance.project = project
        response = super().form_valid(form)

        messenger(
            MESSAGES.APPROVE_PROJECT,
            request=self.request,
            user=self.request.user,
            source=project,
        )

        project.is_locked = False
        project.status = CONTRACTING
        project.save(update_fields=['is_locked', 'status'])

        return response


@method_decorator(staff_required, name='dispatch')
class RejectionView(DelegatedViewMixin, UpdateView):
    context_name = 'rejection_form'
    form_class = RejectionForm
    model = Project

    def form_valid(self, form):
        messenger(
            MESSAGES.REQUEST_PROJECT_CHANGE,
            request=self.request,
            user=self.request.user,
            source=self.object,
            comment=form.cleaned_data['comment'],
        )

        self.object.is_locked = False
        self.object.save(update_fields=['is_locked'])

        return redirect(self.object)


@method_decorator(staff_required, name='dispatch')
class RemoveDocumentView(DelegatedViewMixin, FormView):
    context_name = 'remove_document_form'
    form_class = RemoveDocumentForm
    model = Project

    def form_valid(self, form):
        document_id = form.cleaned_data["id"]
        project = self.kwargs['object']

        try:
            project.packet_files.get(pk=document_id).delete()
        except PacketFile.DoesNotExist:
            pass

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
            source=self.object,
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


@method_decorator(login_required, name='dispatch')
class UploadContractView(DelegatedViewMixin, CreateView):
    context_name = 'contract_form'
    form_class = UploadContractForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        project = self.kwargs['object']
        is_owner = project.user == request.user
        if not (request.user.is_apply_staff or is_owner):
            raise PermissionDenied

        return response

    def form_valid(self, form):
        project = self.kwargs['object']
        form.instance.project = project

        if self.request.user == project.user:
            form.instance.is_signed = True

        response = super().form_valid(form)

        messenger(
            MESSAGES.UPLOAD_CONTRACT,
            request=self.request,
            user=self.request.user,
            source=project,
        )

        return response


@method_decorator(staff_required, name='dispatch')
class UploadDocumentView(DelegatedViewMixin, CreateView):
    context_name = 'document_form'
    form_class = UploadDocumentForm
    model = Project

    def form_valid(self, form):
        project = self.kwargs['object']
        form.instance.project = project
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPLOAD_DOCUMENT,
            request=self.request,
            user=self.request.user,
            source=project,
            title=form.instance.title
        )

        return response


class AdminProjectDetailView(ActivityContextMixin, DelegateableView, ContractsMixin, DetailView):
    form_views = [
        CommentFormView,
        CreateApprovalView,
        RejectionView,
        RemoveDocumentView,
        SendForApprovalView,
        UpdateLeadView,
        UploadContractView,
        UploadDocumentView,
    ]
    model = Project
    template_name_suffix = '_admin_detail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['approvals'] = self.object.approvals.distinct('by')
        context['approve_contract_form'] = ApproveContractForm()
        context['remaining_document_categories'] = list(self.object.get_missing_document_categories())
        return context


class ApplicantProjectDetailView(ActivityContextMixin, DelegateableView, ContractsMixin, DetailView):
    form_views = [
        CommentFormView,
        UploadContractView,
    ]

    model = Project
    template_name_suffix = '_applicant_detail'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        # This view is only for applicants.
        if project.user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView


class ProjectApprovalEditView(UpdateView):
    form_class = ProjectApprovalForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if not project.editable_by(request.user):
            messages.info(self.request, _('You are not allowed to edit the project at this time'))
            return redirect(project)
        return super().dispatch(request, *args, **kwargs)


class ApplicantProjectEditView(UpdateView):
    form_class = ProjectEditForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        # This view is only for applicants.
        if project.user != request.user:
            raise PermissionDenied

        if not project.editable_by(request.user):
            messages.info(self.request, _('You are not allowed to edit the project at this time'))
            return redirect(project)

        return super().dispatch(request, *args, **kwargs)


class ProjectEditView(ViewDispatcher):
    admin_view = ProjectApprovalEditView
    applicant_view = ApplicantProjectEditView
