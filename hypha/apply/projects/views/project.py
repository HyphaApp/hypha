import datetime
import io
from copy import copy

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import Http404, HttpResponse
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
    contracting_approver_required,
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
    ChangePAFStatusForm,
    ChangeProjectStatusForm,
    FinalApprovalForm,
    ProjectApprovalForm,
    RemoveDocumentForm,
    SelectDocumentForm,
    SetPendingForm,
    StaffUploadContractForm,
    UpdateProjectLeadForm,
    UploadContractForm,
    UploadDocumentForm,
)
from ..models.payment import Invoice
from ..models.project import (
    APPROVE,
    COMMITTED,
    CONTRACTING,
    IN_PROGRESS,
    PROJECT_STATUS_CHOICES,
    REQUEST_CHANGE,
    WAITING_FOR_APPROVAL,
    Contract,
    PacketFile,
    PAFApprovals,
    PAFReviewersRole,
    Project,
    ProjectSettings,
)
from ..models.report import Report
from ..permissions import has_permission
from ..tables import InvoiceListTable, ProjectsListTable, ReportListTable
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

        messenger(
            MESSAGES.SEND_FOR_APPROVAL,
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

        if not PAFReviewersRole.objects.all().exists():
            project.ready_for_final_approval = True
            project.save(update_fields={'ready_for_final_approval'})
            # notify final approver if there is no Project Reviewer roles exist
            messenger(
                MESSAGES.PROJECT_FINAL_APPROVAL,
                request=self.request,
                user=self.request.user,
                source=self.object,
            )

        return response


@method_decorator(contracting_approver_required, name='dispatch')
class FinalApprovalView(DelegatedViewMixin, UpdateView):
    form_class = FinalApprovalForm
    context_name = 'final_approval_form'
    model = Project

    def form_valid(self, form):
        project = self.object
        old_stage = project.get_status_display()

        response = super().form_valid(form)

        comment = form.cleaned_data.get('comment', '')
        status = form.cleaned_data['final_approval_status']

        if status == REQUEST_CHANGE:
            project.status = COMMITTED
            project.is_locked = False
            project.ready_for_final_approval = False
            project.save(update_fields=['status', 'is_locked', 'ready_for_final_approval'])
            project.paf_approvals.all().update(approved=False)  # Approvers should look into it again.

            project_status_message = _(
                '<p>{user} request changes the Project and update status to {project_status}.</p>').format(
                user=self.request.user,
                project_status=project.status
            )

            Activity.objects.create(
                user=self.request.user,
                type=ACTION,
                source=project,
                timestamp=timezone.now(),
                message=project_status_message,
                visibility=ALL,
            )

            messenger(
                MESSAGES.REQUEST_PROJECT_CHANGE,
                request=self.request,
                user=self.request.user,
                source=self.object,
                comment=comment,
            )
            return response

        messenger(
            MESSAGES.APPROVE_PROJECT,
            request=self.request,
            user=self.request.user,
            source=project,
        )

        project.is_locked = True
        project.status = CONTRACTING
        project.ready_for_final_approval = False
        project.save(update_fields=['is_locked', 'status', 'ready_for_final_approval'])

        project_status_message = _(
            '<p>{user} approved the Project and update status to {project_status}.</p>').format(
            user=self.request.user,
            project_status=project.status
        )

        Activity.objects.create(
            user=self.request.user,
            type=ACTION,
            source=project,
            timestamp=timezone.now(),
            message=project_status_message,
            visibility=ALL,
        )

        messenger(
            MESSAGES.PROJECT_TRANSITION,
            request=self.request,
            user=self.request.user,
            source=project,
            related=old_stage,
        )

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

        # Only send created_project mail first time lead is set.
        if not old_lead:
            messenger(
                MESSAGES.CREATED_PROJECT,
                request=self.request,
                user=self.request.user,
                source=project,
                related=project.submission,
            )

        messenger(
            MESSAGES.UPDATE_PROJECT_LEAD,
            request=self.request,
            user=self.request.user,
            source=project,
            related=old_lead or 'Unassigned',
        )

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
            if not latest_contract.is_signed:
                contract_to_sign = latest_contract
            elif not latest_contract.approver:
                contract_to_approve = latest_contract

        context = super().get_context_data(**kwargs)
        context['contract_to_approve'] = contract_to_approve
        context['contract_to_sign'] = contract_to_sign
        context['contracts'] = contracts.approved()
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

        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


@method_decorator(login_required, name='dispatch')
class UploadContractView(DelegatedViewMixin, CreateView):
    context_name = 'contract_form'
    model = Project

    def dispatch(self, request, *args, **kwargs):
        project = self.kwargs['object']
        permission, _ = has_permission('contract_upload', request.user, object=project)
        if permission:
            return super().dispatch(request, *args, **kwargs)

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
            related=form.instance,
        )

        return response


# PROJECT VIEW

@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
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
            self.object.status = COMMITTED
            self.object.save(update_fields=['status'])

            messenger(
                MESSAGES.REQUEST_PROJECT_CHANGE,
                request=self.request,
                user=self.request.user,
                source=self.object,
                comment=comment,
            )
        elif paf_status == APPROVE:
            paf_approval.approved = True
            paf_approval.save(update_fields=['approved'])
            project_settings = ProjectSettings.for_request(self.request)
            if project_settings.paf_approval_sequential:
                # notify next approver
                if self.object.paf_approvals.filter(approved=False).exists():
                    messenger(
                        MESSAGES.APPROVE_PAF,
                        request=self.request,
                        user=self.request.user,
                        source=self.object,
                    )

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
            self.object.ready_for_final_approval = True
            self.object.save(update_fields={'ready_for_final_approval'})
            # notify final approver if project is open for final approval
            messenger(
                MESSAGES.PROJECT_FINAL_APPROVAL,
                request=self.request,
                user=self.request.user,
                source=self.object,
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
        return response


class BaseProjectDetailView(ReportingMixin, DetailView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = PROJECT_STATUS_CHOICES
        context['current_status_index'] = [status for status, _ in PROJECT_STATUS_CHOICES].index(self.object.status)
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
        FinalApprovalView,
        RemoveDocumentView,
        SelectDocumentView,
        SendForApprovalView,
        ReportFrequencyUpdate,
        UpdateLeadView,
        UploadContractView,
        UploadDocumentView,
        ChangePAFStatusView,
        ChangeProjectstatusView,
    ]
    model = Project
    template_name_suffix = '_admin_detail'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_settings = ProjectSettings.for_request(self.request)
        context['paf_approval_sequential'] = project_settings.paf_approval_sequential
        context['paf_approvals'] = PAFApprovals.objects.filter(project=self.object)
        context['remaining_document_categories'] = list(self.object.get_missing_document_categories())

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
    ]

    model = Project
    template_name_suffix = '_detail'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if project.user != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


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


# PROJECT EDIT

@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectDetailApprovalView(DelegateableView, DetailView):
    form_views = [
        ChangePAFStatusView
    ]
    model = Project
    template_name_suffix = '_approval_detail'


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

    def get_supporting_documents(self, project):
        documents_dict = {}
        for packet_file in project.packet_files.all():
            documents_dict[packet_file.title] = self.request.build_absolute_uri(
                reverse('apply:projects:document', kwargs={'pk': project.id, 'file_pk': packet_file.id})
            )
        return documents_dict


@method_decorator(staff_or_finance_or_contracting_required, name='dispatch')
class ProjectApprovalEditView(BaseStreamForm, UpdateView):
    submission_form_class = ProjectApprovalForm
    model = Project
    template_name = 'application_projects/project_approval_form.html'

    def buttons(self):
        yield ('submit', 'primary', _('Submit'))

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if not project.editable_by(request.user):
            messages.info(self.request, _('You are not allowed to edit the project at this time'))
            return redirect(project)
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def approval_form(self):
        # fetching from the fund directly instead of going through round
        approval_form = self.object.submission.page.specific.approval_forms.first()  # picking up the first one

        return approval_form

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            title=self.object.title,
            buttons=self.buttons(),
            approval_form_exists=True if self.approval_form else False,
            **kwargs
        )

    def get_defined_fields(self):
        approval_form = self.approval_form
        if approval_form:
            return approval_form.form.form_fields
        return self.object.get_defined_fields()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.approval_form:
            fields = self.approval_form.form.get_form_fields()
        else:
            fields = {}

        kwargs['extra_fields'] = fields
        kwargs['initial'].update(self.object.raw_data)
        return kwargs

    def form_valid(self, form):
        try:
            form_fields = self.approval_form.form.form_fields
        except AttributeError:
            form_fields = []

        form.instance.form_fields = form_fields

        return super().form_valid(form)


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
