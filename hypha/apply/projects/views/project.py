import datetime
import io
from copy import copy

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin
from docx import Document
from htmldocx import HtmlToDocx
from xhtml2pdf import pisa

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.activity.models import ACTION, ALL, COMMENT, Activity
from hypha.apply.activity.views import ActivityContextMixin, CommentFormView
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.users.decorators import (
    staff_or_finance_or_contracting_required,
    staff_or_finance_required,
    staff_required,
)
from hypha.apply.utils.models import PDFPageSettings
from hypha.apply.utils.storage import PrivateMediaView
from hypha.apply.utils.views import DelegateableView, DelegatedViewMixin, ViewDispatcher

from ..files import get_files
from ..filters import InvoiceListFilter, ProjectListFilter, ReportListFilter
from ..forms import (
    ApproveContractForm,
    ApproversForm,
    AssignApproversForm,
    ChangePAFStatusForm,
    ChangeProjectStatusForm,
    ProjectApprovalForm,
    ProjectSOWForm,
    RemoveContractDocumentForm,
    RemoveDocumentForm,
    SelectDocumentForm,
    SetPendingForm,
    SubmitContractDocumentsForm,
    UpdateProjectLeadForm,
    UploadContractDocumentForm,
    UploadContractForm,
    UploadDocumentForm,
)
from ..models.payment import Invoice
from ..models.project import (
    APPROVE,
    CONTRACTING,
    DRAFT,
    IN_PROGRESS,
    PROJECT_ACTION_MESSAGE_TAG,
    PROJECT_STATUS_CHOICES,
    REQUEST_CHANGE,
    WAITING_FOR_APPROVAL,
    Contract,
    ContractDocumentCategory,
    ContractPacketFile,
    DocumentCategory,
    PacketFile,
    PAFApprovals,
    Project,
    ProjectSettings,
)
from ..models.report import Report
from ..permissions import has_permission
from ..tables import InvoiceListTable, ProjectsListTable, ReportListTable
from ..views.payment import ChangeInvoiceStatusView
from .report import ReportFrequencyUpdate, ReportingMixin


@method_decorator(staff_required, name='dispatch')
class SendForApprovalView(DelegatedViewMixin, UpdateView):
    context_name = 'request_approval_form'
    form_class = SetPendingForm
    model = Project

    def form_valid(self, form):
        project = self.kwargs['object']
        old_stage = project.get_status_display()

        response = super().form_valid(form)

        project_settings = ProjectSettings.for_request(self.request)

        paf_approvals = self.object.paf_approvals.filter(approved=False)

        if project_settings.paf_approval_sequential:
            if paf_approvals:
                user = paf_approvals.first().user
                if user:
                    # notify only if first user/approver is updated
                    messenger(
                        MESSAGES.SEND_FOR_APPROVAL,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
                else:
                    messenger(
                        MESSAGES.ASSIGN_PAF_APPROVER,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
        else:
            if paf_approvals.filter(user__isnull=False).exists():
                messenger(
                    MESSAGES.SEND_FOR_APPROVAL,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                )
            if paf_approvals.filter(user__isnull=True).exists():
                messenger(
                    MESSAGES.ASSIGN_PAF_APPROVER,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                )

        project.status = WAITING_FOR_APPROVAL
        project.save(update_fields=['status'])

        messenger(
            MESSAGES.PROJECT_TRANSITION,
            request=self.request,
            user=self.request.user,
            source=project,
            related=old_stage,
        )

        messages.success(self.request, _("PAF has been submitted for approval"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response


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

        messages.success(self.request, _("Document has been uploaded"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)

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

        messages.success(self.request, _("Document has been removed"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return redirect(project)


@method_decorator(login_required, name='dispatch')
class RemoveContractDocumentView(DelegatedViewMixin, FormView):
    context_name = 'remove_contract_document_form'
    form_class = RemoveContractDocumentForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_applicant:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        document_id = form.cleaned_data["id"]
        project = self.kwargs['object']

        try:
            project.contract_packet_files.get(pk=document_id).delete()
        except ContractPacketFile.DoesNotExist:
            pass

        messages.success(self.request, _("Contracting document has been removed"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)

        return redirect(project)


@method_decorator(login_required, name='dispatch')
class SelectDocumentView(DelegatedViewMixin, CreateView):
    form_class = SelectDocumentForm
    context_name = 'select_document_form'
    model = PacketFile

    @property
    def should_show(self):
        return bool(self.files)

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
        old_lead = copy(self.get_object().lead)

        response = super().form_valid(form)
        project = form.instance

        messenger(
            MESSAGES.UPDATE_PROJECT_LEAD,
            request=self.request,
            user=self.request.user,
            source=project,
            related=old_lead or 'Unassigned',
        )

        messages.success(self.request, _('Lead has been updated'), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response


# CONTRACTS

class ContractsMixin:
    def get_context_data(self, **kwargs):
        project = self.get_object()
        contracts = project.contracts.select_related(
            'approver',
        ).order_by('-created_at')

        latest_contract = contracts.first()
        contract_to_approve = None
        contract_to_sign = None
        if latest_contract:
            if not latest_contract.signed_by_applicant:
                contract_to_sign = latest_contract
            elif not latest_contract.approver:
                contract_to_approve = latest_contract

        context = super().get_context_data(**kwargs)
        context['contract_to_approve'] = contract_to_approve
        context['contract_to_sign'] = contract_to_sign
        context['contracts'] = contracts.approved()
        context['contract'] = latest_contract
        return context


@method_decorator(staff_required, name='dispatch')
class ApproveContractView(DelegatedViewMixin, UpdateView):
    form_class = ApproveContractForm
    model = Contract
    context_name = 'approve_contract_form'

    def get_object(self):
        project = self.get_parent_object()
        latest_contract = project.contracts.order_by('-created_at').first()
        if latest_contract and not latest_contract.approver:
            return latest_contract

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        kwargs.pop('user')
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, mark_safe(_('Sorry something went wrong') + form.errors.as_ul()))
        return super().form_invalid(form)

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.approver = self.request.user
            form.instance.approved_at = timezone.now()
            form.instance.project = self.project
            response = super().form_valid(form)

            old_stage = self.project.get_status_display()

            messenger(
                MESSAGES.APPROVE_CONTRACT,
                request=self.request,
                user=self.request.user,
                source=self.project,
                related=self.object,
            )

            self.project.status = IN_PROGRESS
            self.project.save(update_fields=['status'])

            messenger(
                MESSAGES.PROJECT_TRANSITION,
                request=self.request,
                user=self.request.user,
                source=self.project,
                related=old_stage,
            )

        messages.success(self.request, _("Contractor documents have been approved."
                                         " You can receive invoices from applicant now."),
                         extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


@method_decorator(login_required, name='dispatch')
class UploadContractView(DelegatedViewMixin, CreateView):
    context_name = 'contract_form'
    model = Project
    form_class = UploadContractForm

    def dispatch(self, request, *args, **kwargs):
        project = self.kwargs['object']
        permission, _ = has_permission('contract_upload', request.user, object=project)
        if permission:
            return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance')
        kwargs.pop('user')
        return kwargs

    def form_valid(self, form):
        project = self.kwargs['object']

        if project.contracts.exists():
            form.instance = project.contracts.order_by('created_at').first()

        form.instance.project = project

        if self.request.user == project.user:
            form.instance.signed_by_applicant = True
            form.instance.uploaded_by_applicant_at = timezone.now()
            messages.success(self.request, _("Countersigned contract uploaded"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        elif self.request.user.is_contracting:
            form.instance.uploaded_by_contractor_at = timezone.now()
            messages.success(self.request, _("Signed contract uploaded"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)

        response = super().form_valid(form)

        if self.request.user != project.user:
            messenger(
                MESSAGES.UPLOAD_CONTRACT,
                request=self.request,
                user=self.request.user,
                source=project,
                related=form.instance,
            )

        return response


@method_decorator(login_required, name='dispatch')
class SubmitContractDocumentsView(DelegatedViewMixin, UpdateView):
    context_name = 'submit_contract_documents_form'
    model = Project
    form_class = SubmitContractDocumentsForm

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if list(project.get_missing_contract_document_categories()):
            raise PermissionDenied
        contract = project.contracts.order_by('-created_at').first()
        permission, _ = has_permission('submit_contract_documents', request.user, object=project,
                                       raise_exception=True, contract=contract)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = self.kwargs['object']
        response = super().form_valid(form)

        project.submitted_contract_documents = True
        project.save(update_fields=['submitted_contract_documents'])

        messenger(
            MESSAGES.SUBMIT_CONTRACT_DOCUMENTS,
            request=self.request,
            user=self.request.user,
            source=project,
        )

        messages.success(self.request, _("Contract documents submitted"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response


@method_decorator(login_required, name='dispatch')
class UploadContractDocumentView(DelegatedViewMixin, CreateView):
    form_class = UploadContractDocumentForm
    model = Project
    context_name = 'contract_document_form'

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

        messages.success(self.request, _("Contracting document has been uploaded"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response


# PROJECT VIEW

@method_decorator(login_required, name='dispatch')
class ChangePAFStatusView(DelegatedViewMixin, UpdateView):
    form_class = ChangePAFStatusForm
    context_name = 'change_paf_status'
    model = Project

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        permission, _ = has_permission(
            'paf_status_update', self.request.user, object=self.object, raise_exception=True, request=request
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        paf_approval = self.request.user.paf_approvals.filter(project=self.object, approved=False).first()
        paf_status = form.cleaned_data.get('paf_status')
        comment = form.cleaned_data.get('comment', '')

        paf_status_update_message = _('<p>{role} has updated PAF status to {paf_status}.</p>').format(
            role=paf_approval.paf_reviewer_role.label, paf_status=paf_status)
        Activity.objects.create(
            user=self.request.user,
            type=ACTION,
            source=self.object,
            timestamp=timezone.now(),
            message=paf_status_update_message,
            visibility=ALL,
        )

        if paf_status == REQUEST_CHANGE:
            self.object.status = DRAFT
            self.object.save(update_fields=['status'])

            messenger(
                MESSAGES.REQUEST_PROJECT_CHANGE,
                request=self.request,
                user=self.request.user,
                source=self.object,
                comment=comment,
            )
            messages.success(self.request, _("PAF status has been updated"),
                             extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        elif paf_status == APPROVE:
            paf_approval.approved = True
            paf_approval.approved_at = timezone.now()
            paf_approval.save(update_fields=['approved', 'approved_at'])
            project_settings = ProjectSettings.for_request(self.request)
            if project_settings.paf_approval_sequential:
                # notify next approver
                if self.object.paf_approvals.filter(approved=False).exists():
                    if self.object.paf_approvals.filter(approved=False).first().user:
                        messenger(
                            MESSAGES.APPROVE_PAF,
                            request=self.request,
                            user=self.request.user,
                            source=self.object,
                        )
                    else:
                        messenger(
                            MESSAGES.ASSIGN_PAF_APPROVER,
                            request=self.request,
                            user=self.request.user,
                            source=self.object,
                        )
            messages.success(self.request, _("PAF has been approved"),
                             extra_tags=PROJECT_ACTION_MESSAGE_TAG)

        if form.cleaned_data['comment']:

            comment = f"<p>{form.cleaned_data['comment']}.</p>"

            message = paf_status_update_message + comment

            Activity.objects.create(
                user=self.request.user,
                type=COMMENT,
                source=self.object,
                timestamp=timezone.now(),
                message=message,
                visibility=ALL,
            )

        if self.object.is_approved_by_all_paf_reviewers:
            old_stage = self.object.get_status_display()
            self.object.is_locked = True
            self.object.status = CONTRACTING
            self.object.save(update_fields=['is_locked', 'status'])

            messenger(
                MESSAGES.PROJECT_TRANSITION,
                request=self.request,
                user=self.request.user,
                source=self.object,
                related=old_stage,
            )
        return response


class ChangeProjectstatusView(DelegatedViewMixin, UpdateView):
    """
    Project status can be updated manually only in 'IN PROGRESS, CLOSING and COMPLETE' state.
    """
    form_class = ChangeProjectStatusForm
    context_name = 'change_project_status'
    model = Project

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        permission, _ = has_permission('project_status_update', request.user, self.project, raise_exception=True)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        old_stage = self.project.get_status_display()

        response = super().form_valid(form)

        comment = form.cleaned_data.get('comment', '')

        if comment:
            Activity.objects.create(
                user=self.request.user,
                type=COMMENT,
                source=self.object,
                timestamp=timezone.now(),
                message=comment,
                visibility=ALL,
            )

        messenger(
            MESSAGES.PROJECT_TRANSITION,
            request=self.request,
            user=self.request.user,
            source=self.object,
            related=old_stage,
        )

        messages.success(self.request, _("Project status has been updated"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response


@method_decorator(login_required, name='dispatch')
class UpdateAssignApproversView(DelegatedViewMixin, UpdateView):
    context_name = 'assign_approvers_form'
    form_class = AssignApproversForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        permission, _ = has_permission('update_paf_assigned_approvers', request.user, self.project,
                                       raise_exception=True, request=request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        from ..forms.project import get_latest_project_paf_approval_via_roles
        project = self.kwargs['object']

        response = super().form_valid(form)

        paf_approval = get_latest_project_paf_approval_via_roles(project=project, roles=self.request.user.groups.all())

        if paf_approval.user:
            messenger(
                MESSAGES.APPROVE_PAF,
                request=self.request,
                user=self.request.user,
                source=self.object,
            )
        else:
            messenger(
                MESSAGES.ASSIGN_PAF_APPROVER,
                request=self.request,
                user=self.request.user,
                source=self.object,
            )

        return response


class UpdatePAFApproversView(DelegatedViewMixin, UpdateView):
    context_name = 'update_approvers_form'
    form_class = ApproversForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        permission, _ = has_permission('paf_approvers_update', request.user, self.project, raise_exception=True, request=request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        project = self.kwargs['object']

        project_settings = ProjectSettings.for_request(self.request)
        old_approvers = None
        if self.object.paf_approvals.exists():
            old_approvers = list(project.paf_approvals.filter(approved=False).values_list('user__id', flat=True))

        response = super().form_valid(form)

        paf_approvals = self.object.paf_approvals.filter(approved=False)

        if old_approvers and paf_approvals:
            # if approvers exists already
            if project_settings.paf_approval_sequential:
                user = paf_approvals.first().user
                if user and user.id != old_approvers[0]:
                    # notify only if first user/approver is updated
                    messenger(
                        MESSAGES.APPROVE_PAF,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
                elif not user:
                    messenger(
                        MESSAGES.ASSIGN_PAF_APPROVER,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
            else:
                if paf_approvals.filter(user__isnull=False).exists():
                    messenger(
                        MESSAGES.APPROVE_PAF,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
                if paf_approvals.filter(user__isnull=True).exists():
                    messenger(
                        MESSAGES.ASSIGN_PAF_APPROVER,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )
        elif paf_approvals:
            if paf_approvals.filter(user__isnull=False).exists():
                messenger(
                    MESSAGES.APPROVE_PAF,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                )
            if paf_approvals.filter(user__isnull=True).exists():
                messenger(
                    MESSAGES.ASSIGN_PAF_APPROVER,
                    request=self.request,
                    user=self.request.user,
                    source=self.object,
                )

        messages.success(self.request, _("PAF approvers have been updated"), extra_tags=PROJECT_ACTION_MESSAGE_TAG)
        return response


class BaseProjectDetailView(ReportingMixin, DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = PROJECT_STATUS_CHOICES
        context['current_status_index'] = [status for status, _ in PROJECT_STATUS_CHOICES].index(self.object.status)
        context['supporting_documents_configured'] = True if DocumentCategory.objects.count() else False
        context['contracting_documents_configured'] = True if ContractDocumentCategory.objects.count() else False
        return context


class AdminProjectDetailView(
    ActivityContextMixin,
    DelegateableView,
    ContractsMixin,
    BaseProjectDetailView,
):
    form_views = [
        ApproveContractView,
        CommentFormView,
        RemoveDocumentView,
        SelectDocumentView,
        SendForApprovalView,
        UpdatePAFApproversView,
        ReportFrequencyUpdate,
        UpdateLeadView,
        UploadContractView,
        UploadDocumentView,
        UpdateAssignApproversView,
        ChangePAFStatusView,
        ChangeProjectstatusView,
        ChangeInvoiceStatusView,
    ]
    model = Project
    template_name_suffix = '_admin_detail'

    def dispatch(self, *args, **kwargs):
        project = self.get_object()
        permission, _ = has_permission('project_access', self.request.user, object=project, raise_exception=True)
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_settings = ProjectSettings.for_request(self.request)
        context['project_settings'] = project_settings
        context['paf_approvals'] = PAFApprovals.objects.filter(project=self.object)
        context['all_document_categories'] = DocumentCategory.objects.all()
        context['remaining_document_categories'] = DocumentCategory.objects.filter(~Q(packet_files__project=self.object))
        context['all_contract_document_categories'] = ContractDocumentCategory.objects.all()
        context['remaining_contract_document_categories'] = ContractDocumentCategory.objects.filter(~Q(contract_packet_files__project=self.object))

        if self.object.is_in_progress and not self.object.report_config.disable_reporting:
            # Current due report can be none for ONE_TIME,
            # In case of ONE_TIME, either reporting is already completed(last_report exists)
            # or there should be a current_due_report.
            if self.object.report_config.current_due_report():
                context['report_data'] = {
                    'startDate': self.object.report_config.current_due_report().start_date,
                    'projectEndDate': self.object.end_date,
                }
            else:
                context['report_data'] = {
                    'startDate': self.object.report_config.last_report().start_date,
                    'projectEndDate': self.object.end_date,
                }
        return context


class ApplicantProjectDetailView(
    ActivityContextMixin,
    DelegateableView,
    ContractsMixin,
    BaseProjectDetailView,
):
    form_views = [
        CommentFormView,
        SelectDocumentView,
        UploadContractView,
        UploadDocumentView,
        UploadContractDocumentView,
        RemoveContractDocumentView,
        SubmitContractDocumentsView,
    ]

    model = Project
    template_name_suffix = '_detail'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        permission, _ = has_permission('project_access', request.user, object=project, raise_exception=True)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_contract_document_categories'] = ContractDocumentCategory.objects.all()
        context['remaining_contract_document_categories'] = ContractDocumentCategory.objects.filter(~Q(contract_packet_files__project=self.object))
        return context


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    finance_view = AdminProjectDetailView
    contracting_view = AdminProjectDetailView
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

        if self.request.user.id in self.project.paf_approvals.filter(approved=False).values_list('user__id', flat=True):
            return True

        return False


@method_decorator(login_required, name='dispatch')
class CategoryTemplatePrivateMediaView(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        project_pk = self.kwargs['pk']
        self.project = get_object_or_404(Project, pk=project_pk)
        self.category_type = kwargs['type']
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        if self.category_type == "project_document":
            category = DocumentCategory.objects.get(pk=kwargs['category_pk'])
        elif self.category_type == "contract_document":
            category = ContractDocumentCategory.objects.get(pk=kwargs['category_pk'])
        else:
            raise Http404
        if not category.template:
            raise Http404
        return category.template

    def test_func(self):
        if self.category_type == "project_document":
            if self.request.user.is_apply_staff or self.request.user.is_contracting or self.request.user.is_finance:
                return True
        elif self.category_type == "contract_document":
            if self.request.user.is_applicant:
                return True
        return False


@method_decorator(login_required, name='dispatch')
class ContractPrivateMediaView(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        project_pk = self.kwargs['pk']
        self.project = get_object_or_404(Project, pk=project_pk)
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        document = Contract.objects.get(pk=kwargs['file_pk'])
        if document.project != self.project:
            raise Http404
        return document.file

    def test_func(self):
        if self.request.user.is_apply_staff or self.request.user.is_contracting:
            return True

        if self.request.user == self.project.user:
            return True

        return False


@method_decorator(login_required, name='dispatch')
class ContractDocumentPrivateMediaView(UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        project_pk = self.kwargs['pk']
        self.project = get_object_or_404(Project, pk=project_pk)
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        document = ContractPacketFile.objects.get(pk=kwargs['file_pk'])
        if document.project != self.project:
            raise Http404
        return document.document

    def test_func(self):
        if self.request.user.is_apply_staff or self.request.user.is_contracting:
            return True

        if self.request.user == self.project.user:
            return True

        return False


# PROJECT APPROVAL FORM VIEWS

@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectDetailApprovalView(DelegateableView, DetailView):
    form_views = [
        ChangePAFStatusView
    ]
    model = Project
    template_name_suffix = '_approval_detail'


@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectSOWView(DetailView):
    model = Project
    template_name_suffix = '_sow_detail'


@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectSOWDownloadView(SingleObjectMixin, View):
    model = Project

    def get(self, request, *args, **kwargs):
        export_type = kwargs.get('export_type', 'pdf')
        self.object = self.get_object()
        context = {}
        context['sow_data'] = self.get_sow_data_with_field(self.object)
        context['org_name'] = settings.ORG_LONG_NAME
        context['title'] = self.object.title
        context['project_link'] = self.request.build_absolute_uri(
            reverse('apply:projects:detail', kwargs={'pk': self.object.id})
        )
        template_path = 'application_projects/sow_export.html'

        if export_type == 'pdf':
            pdf_page_settings = PDFPageSettings.for_request(request)

            context['show_footer'] = True
            context['export_date'] = datetime.date.today().strftime("%b %d, %Y")
            context['export_user'] = request.user
            context['pagesize'] = pdf_page_settings.download_page_size

            return self.render_as_pdf(
                context=context,
                template=get_template(template_path),
                filename=self.get_slugified_file_name(export_type)
            )
        elif export_type == 'docx':
            context['show_footer'] = False

            return self.render_as_docx(
                context=context,
                template=get_template(template_path),
                filename=self.get_slugified_file_name(export_type)
            )
        else:
            raise Http404(f"{export_type} type not supported at the moment")

    def render_as_pdf(self, context, template, filename):
        html = template.render(context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        pisa_status = pisa.CreatePDF(
            html, dest=response, encoding='utf-8', raise_exception=True)
        if pisa_status.err:
            # :todo: needs to handle it in a better way
            raise Http404('PDF type not supported at the moment')
        return response

    def render_as_docx(self, context, template, filename):
        html = template.render(context)

        buf = io.BytesIO()
        document = Document()
        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html, document)
        document.save(buf)

        response = HttpResponse(buf.getvalue(), content_type='application/docx')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def get_slugified_file_name(self, export_type):
        return f"{datetime.date.today().strftime('%Y%m%d')}-{slugify(self.object.title)}.{export_type}"

    def get_sow_data_with_field(self, project):
        data_dict = {}
        if project.submission.page.specific.sow_forms.exists() and project.sow:
            form_data_dict = project.sow.form_data
            for field in project.sow.form_fields.raw_data:
                if field['id'] in form_data_dict.keys():
                    if isinstance(field['value'], dict) and 'field_label' in field['value']:
                        data_dict[field['value']['field_label']] = form_data_dict[field['id']]

        return data_dict


@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectDetailDownloadView(SingleObjectMixin, View):
    model = Project

    def get(self, request, *args, **kwargs):
        export_type = kwargs.get('export_type', None)
        self.object = self.get_object()
        context = self.get_paf_download_context()
        template_path = 'application_projects/paf_export.html'

        if export_type == 'pdf':
            pdf_page_settings = PDFPageSettings.for_request(request)

            context['show_footer'] = True
            context['export_date'] = datetime.date.today().strftime("%b %d, %Y")
            context['export_user'] = request.user
            context['pagesize'] = pdf_page_settings.download_page_size

            return self.render_as_pdf(
                context=context,
                template=get_template(template_path),
                filename=self.get_slugified_file_name(export_type)
            )
        elif export_type == 'docx':
            context['show_footer'] = False

            return self.render_as_docx(
                context=context,
                template=get_template(template_path),
                filename=self.get_slugified_file_name(export_type)
            )
        else:
            raise Http404(f"{export_type} type not supported at the moment")

    def render_as_pdf(self, context, template, filename):
        html = template.render(context)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={filename}'

        pisa_status = pisa.CreatePDF(
            html, dest=response, encoding='utf-8', raise_exception=True)
        if pisa_status.err:
            # :todo: needs to handle it in a better way
            raise Http404('PDF type not supported at the moment')
        return response

    def render_as_docx(self, context, template, filename):
        html = template.render(context)

        buf = io.BytesIO()
        document = Document()
        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html, document)
        document.save(buf)

        response = HttpResponse(buf.getvalue(), content_type='application/docx')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    def get_slugified_file_name(self, export_type):
        return f"{datetime.date.today().strftime('%Y%m%d')}-{slugify(self.object.title)}.{export_type}"

    def get_paf_download_context(self):
        context = {}
        context['id'] = self.object.id
        context['title'] = self.object.title
        context['project_link'] = self.request.build_absolute_uri(
            reverse('apply:projects:detail', kwargs={'pk': self.object.id})
        )
        context['proposed_start_date'] = self.object.proposed_start
        context['proposed_end_date'] = self.object.proposed_end
        context['contractor_name'] = self.object.vendor.contractor_name if self.object.vendor else None
        context['total_amount'] = self.object.value

        context['approvals'] = self.object.paf_approvals.all()
        context['paf_data'] = self.get_paf_data_with_field(self.object)
        context['sow_data'] = self.get_sow_data_with_field(self.object)
        context['submission'] = self.object.submission
        context['submission_link'] = self.request.build_absolute_uri(
            reverse('apply:submissions:detail', kwargs={'pk': self.object.submission.id})
        )
        context['supporting_documents'] = self.get_supporting_documents(self.object)
        context['org_name'] = settings.ORG_LONG_NAME
        return context

    def get_paf_data_with_field(self, project):
        data_dict = {}
        form_data_dict = project.form_data
        for field in project.form_fields.raw_data:
            if field['id'] in form_data_dict.keys():
                if isinstance(field['value'], dict) and 'field_label' in field['value']:
                    data_dict[field['value']['field_label']] = form_data_dict[field['id']]

        return data_dict

    def get_sow_data_with_field(self, project):
        data_dict = {}
        if project.submission.page.specific.sow_forms.exists() and project.sow:
            form_data_dict = project.sow.form_data
            for field in project.sow.form_fields.raw_data:
                if field['id'] in form_data_dict.keys():
                    if isinstance(field['value'], dict) and 'field_label' in field['value']:
                        data_dict[field['value']['field_label']] = form_data_dict[field['id']]

        return data_dict

    def get_supporting_documents(self, project):
        documents_dict = {}
        for packet_file in project.packet_files.all():
            documents_dict[packet_file.title] = self.request.build_absolute_uri(
                reverse('apply:projects:document', kwargs={'pk': project.id, 'file_pk': packet_file.id})
            )
        return documents_dict


@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectApprovalFormEditView(BaseStreamForm, UpdateView):
    model = Project
    template_name = 'application_projects/project_approval_form.html'
    # Remember to assign paf_form first and then sow_form, else get_defined_fields method may provide unexpected results
    paf_form = None
    sow_form = None

    def buttons(self):
        yield ('submit', 'primary', _('Submit'))

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.editable_by(request.user):
            messages.info(self.request, _('You are not allowed to edit the project at this time'))
            return redirect(self.object)
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def approval_form(self):
        # fetching from the fund directly instead of going through round
        approval_form = self.object.submission.page.specific.approval_forms.first()  # picking up the first one

        return approval_form

    @cached_property
    def approval_sow_form(self):
        # fetching from the fund directly instead of going through round
        approval_sow_form = self.object.submission.page.specific.sow_forms.first()  # picking up the first one

        return approval_sow_form

    def get_form_class(self, form_class,  draft=False, form_data=None, user=None):
        return type('WagtailStreamForm', (form_class,), self.get_form_fields(draft, form_data, user))

    def get_paf_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class(ProjectApprovalForm)
        return form_class(**self.get_paf_form_kwargs())

    def get_sow_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class(ProjectSOWForm)
        return form_class(**self.get_sow_form_kwargs())

    def get_context_data(self, **kwargs):
        self.paf_form = self.get_paf_form()
        if self.approval_sow_form:
            self.sow_form = self.get_sow_form()
        return {
            "title": self.object.title,
            "buttons": self.buttons(),
            "approval_form_exists": True if self.approval_form else False,
            "sow_form_exists": True if self.approval_sow_form else False,
            "paf_form": self.paf_form,
            "sow_form": self.sow_form,
            "object": self.object,
            **kwargs
        }

    def get_defined_fields(self):
        approval_form = self.approval_form
        if approval_form and not self.paf_form:
            return approval_form.form.form_fields
        if self.approval_sow_form and self.paf_form and not self.sow_form:
            return self.approval_sow_form.form.form_fields
        return self.object.get_defined_fields()

    def get_paf_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.approval_form:
            fields = self.approval_form.form.get_form_fields()
        else:
            fields = {}

        kwargs['extra_fields'] = fields
        kwargs['initial'].update(self.object.raw_data)
        return kwargs

    def get_sow_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.approval_sow_form:
            fields = self.approval_sow_form.form.get_form_fields()

            kwargs['extra_fields'] = fields
            try:
                sow_instance = self.object.sow
                kwargs['initial'].update({'project': self.object, **sow_instance.raw_data})
            except ObjectDoesNotExist:
                kwargs['initial'].update({'project': self.object})
        return kwargs

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """

        self.paf_form = self.get_paf_form()
        if self.approval_sow_form:
            self.sow_form = self.get_sow_form()
            if self.paf_form.is_valid() and self.sow_form.is_valid():
                # if both forms exists, both needs to be valid together
                try:
                    paf_form_fields = self.approval_form.form.form_fields
                except AttributeError:
                    paf_form_fields = []
                try:
                    sow_form_fields = self.approval_sow_form.form.form_fields
                except AttributeError:
                    sow_form_fields = []

                self.paf_form.save(paf_form_fields=paf_form_fields)
                self.sow_form.save(sow_form_fields=sow_form_fields, project=self.object)
                return HttpResponseRedirect(self.get_success_url())
            else:
                if not self.paf_form.is_valid():
                    return self.form_invalid(self.paf_form)
                return self.form_invalid(self.sow_form)
        else:
            if self.paf_form.is_valid():
                # paf can exist alone also, it needs to be valid
                try:
                    paf_form_fields = self.approval_form.form.form_fields
                except AttributeError:
                    paf_form_fields = []
                self.paf_form.save(paf_form_fields=paf_form_fields)
                return HttpResponseRedirect(self.get_success_url())
            else:
                return self.form_invalid(self.paf_form)



@method_decorator(staff_or_finance_required, name='dispatch')
class ProjectListView(SingleTableMixin, FilterView):
    filterset_class = ProjectListFilter
    queryset = Project.objects.for_table()
    table_class = ProjectsListTable
    template_name = 'application_projects/project_list.html'


@method_decorator(staff_or_finance_required, name='dispatch')
class ProjectOverviewView(TemplateView):
    template_name = 'application_projects/overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.get_projects(self.request)
        context['invoices'] = self.get_invoices(self.request)
        context['reports'] = self.get_reports(self.request)
        context['status_counts'] = self.get_status_counts()
        return context

    def get_reports(self, request):
        reports = Report.objects.for_table().submitted()[:10]
        return {
            'filterset': ReportListFilter(request.GET or None, request=request, queryset=reports),
            'table': ReportListTable(reports, order_by=()),
            'url': reverse('apply:projects:reports:all'),
        }

    def get_projects(self, request):
        projects = Project.objects.for_table()[:10]

        return {
            'filterset': ProjectListFilter(request.GET or None, request=request, queryset=projects),
            'table': ProjectsListTable(projects, order_by=()),
            'url': reverse('apply:projects:all'),
        }

    def get_invoices(self, request):
        invoices = Invoice.objects.order_by('-requested_at')[:10]

        return {
            'filterset': InvoiceListFilter(request.GET or None, request=request, queryset=invoices),
            'table': InvoiceListTable(invoices, order_by=()),
            'url': reverse('apply:projects:invoices'),
        }

    def get_status_counts(self):
        status_counts = dict(
            Project.objects.all().values('status').annotate(
                count=Count('status'),
            ).values_list(
                'status',
                'count',
            )
        )

        return {
            key: {
                'name': display,
                'count': status_counts.get(key, 0),
                'url': reverse_lazy("funds:projects:all") + '?project_status=' + key,
            }
            for key, display in PROJECT_STATUS_CHOICES
        }
