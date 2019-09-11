from copy import copy

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    UpdateView
)

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.activity.views import ActivityContextMixin, CommentFormView
from opentech.apply.users.decorators import approver_required, staff_required
from opentech.apply.utils.storage import PrivateMediaView
from opentech.apply.utils.views import (
    DelegateableView,
    DelegatedViewMixin,
    ViewDispatcher,
)

from ..files import get_files
from ..forms import (
    ApproveContractForm,
    CreateApprovalForm,
    ProjectApprovalForm,
    ProjectEditForm,
    RejectionForm,
    RemoveDocumentForm,
    SelectDocumentForm,
    SetPendingForm,
    StaffUploadContractForm,
    UpdateProjectLeadForm,
    UploadContractForm,
    UploadDocumentForm
)
from ..models import (
    CONTRACTING,
    IN_PROGRESS,
    PROJECT_STATUS_CHOICES,
    Approval,
    Contract,
    PacketFile,
    Project
)
from .payment import RequestPaymentView


# APPROVAL VIEWS

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
class CreateApprovalView(DelegatedViewMixin, CreateView):
    context_name = 'add_approval_form'
    form_class = CreateApprovalForm
    model = Approval

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance')
        return kwargs

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

        project.send_to_compliance(self.request)

        project.is_locked = False
        project.status = CONTRACTING
        project.save(update_fields=['is_locked', 'status'])

        return response


@method_decorator(approver_required, name='dispatch')
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


# PROJECT DOCUMENTS

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
        )

        return response


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


@method_decorator(login_required, name='dispatch')
class SelectDocumentView(DelegatedViewMixin, CreateView):
    form_class = SelectDocumentForm
    context_name = 'select_document_form'
    model = PacketFile

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        for error in form.errors:
            messages.error(self.request, error)

        return redirect(self.project)

    def form_valid(self, form):
        form.instance.project = self.project
        form.instance.name = form.instance.document.name

        response = super().form_valid(form)

        messenger(
            MESSAGES.UPLOAD_DOCUMENT,
            request=self.request,
            user=self.request.user,
            source=self.project,
        )

        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('user')
        kwargs.pop('instance')
        kwargs['existing_files'] = get_files(self.get_parent_object())
        return kwargs


# GENERAL FORM VIEWS

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


# CONTRACTS

class ContractsMixin:
    def get_context_data(self, **kwargs):
        project = self.get_object()
        contracts = (project.contracts.select_related('approver')
                                      .order_by('-created_at'))

        latest_contract = self.get_contract_to_approve(contracts)

        contracts = contracts.filter(is_signed=True, approver__isnull=False)

        if latest_contract:
            contracts = [latest_contract, *contracts]

        context = super().get_context_data(**kwargs)
        context['latest_contract'] = latest_contract
        context['contracts'] = contracts
        return context

    def get_contract_to_approve(self, contracts):
        """If there's a contract to approve, get that"""
        latest = contracts.first()

        if not latest:
            return

        if latest.approver:
            return

        return latest


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


@method_decorator(login_required, name='dispatch')
class UploadContractView(DelegatedViewMixin, CreateView):
    context_name = 'contract_form'
    model = Project

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        project = self.kwargs['object']
        is_owner = project.user == request.user
        if not (request.user.is_apply_staff or is_owner):
            raise PermissionDenied

        return response

    def get_form_class(self):
        if self.request.user.is_apply_staff:
            return StaffUploadContractForm
        return UploadContractForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance')
        kwargs.pop('user')
        return kwargs

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


# PROJECT VIEW

class AdminProjectDetailView(
    ActivityContextMixin,
    DelegateableView,
    ContractsMixin,
    DetailView,
):
    form_views = [
        CommentFormView,
        CreateApprovalView,
        RejectionView,
        RemoveDocumentView,
        RequestPaymentView,
        SelectDocumentView,
        SendForApprovalView,
        UpdateLeadView,
        UploadContractView,
        UploadDocumentView,
    ]
    model = Project
    template_name_suffix = '_admin_detail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = PROJECT_STATUS_CHOICES
        context['current_status_index'] = [status for status, _ in PROJECT_STATUS_CHOICES].index(self.object.status)
        context['approvals'] = self.object.approvals.distinct('by')
        context['approve_contract_form'] = ApproveContractForm()
        context['remaining_document_categories'] = list(self.object.get_missing_document_categories())
        return context


class ApplicantProjectDetailView(ActivityContextMixin, DelegateableView, ContractsMixin, DetailView):
    form_views = [
        CommentFormView,
        RequestPaymentView,
        SelectDocumentView,
        UploadContractView,
    ]

    model = Project
    template_name_suffix = '_applicant_detail'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if project.user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView


@method_decorator(login_required, name='dispatch')
class ProjectPrivateMediaView(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        project_pk = self.kwargs['pk']
        self.project = get_object_or_404(Project, pk=project_pk)
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        document = PacketFile.objects.get(pk=kwargs['file_pk'])
        if document.project != self.project:
            raise Http404
        return document.document

    def test_func(self):
        if self.request.user.is_apply_staff:
            return True

        if self.request.user == self.project.user:
            return True

        return False


# PROJECT EDIT

@method_decorator(staff_required, name='dispatch')
class ProjectDetailSimplifiedView(DetailView):
    model = Project
    template_name_suffix = '_simplified_detail'


class ProjectApprovalEditView(UpdateView):
    form_class = ProjectApprovalForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if not project.editable_by(request.user):
            messages.info(self.request, _('You are not allowed to edit the project at this time'))
            return redirect(project)
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def approval_form(self):
        if self.object.get_defined_fields():
            approval_form = self.object
        else:
            approval_form = self.object.submission.page.specific.approval_form

        return approval_form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.approval_form:
            fields = self.approval_form.get_form_fields()
        else:
            fields = {}

        kwargs['extra_fields'] = fields
        kwargs['initial'].update(self.object.raw_data)
        return kwargs

    def form_valid(self, form):
        try:
            form_fields = self.approval_form.form_fields
        except AttributeError:
            form_fields = []

        form.instance.form_fields = form_fields

        return super().form_valid(form)


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
