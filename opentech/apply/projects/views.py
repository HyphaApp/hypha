import decimal
from copy import copy

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    UpdateView
)

from opentech.apply.activity.messaging import MESSAGES, messenger
from opentech.apply.activity.views import ActivityContextMixin, CommentFormView
from opentech.apply.users.decorators import staff_required
from opentech.apply.utils.storage import PrivateMediaView
from opentech.apply.utils.views import (
    DelegateableView,
    DelegatedViewMixin,
    ViewDispatcher
)

from .files import get_files
from .forms import (
    ApproveContractForm,
    ChangePaymentRequestStatusForm,
    CreateApprovalForm,
    EditPaymentRequestForm,
    ProjectApprovalForm,
    ProjectEditForm,
    RejectionForm,
    RemoveDocumentForm,
    RequestPaymentForm,
    SelectDocumentForm,
    SetPendingForm,
    UpdateProjectLeadForm,
    UploadContractForm,
    UploadDocumentForm
)
from .models import (
    CHANGES_REQUESTED,
    CONTRACTING,
    DECLINED,
    IN_PROGRESS,
    PAID,
    PROJECT_STATUS_CHOICES,
    REQUEST_STATUS_CHOICES,
    SUBMITTED,
    UNDER_REVIEW,
    Approval,
    Contract,
    PacketFile,
    PaymentRequest,
    Project
)


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


class PaymentsMixin:
    def get_context_data(self, **kwargs):
        project = self.get_object()

        payments = {
            'availabe_statuses': REQUEST_STATUS_CHOICES,
            'not_rejected': project.payment_requests.exclude(status=DECLINED),
            'rejected': project.payment_requests.filter(status=DECLINED),
            'totals': self.get_totals(project),
        }

        context = super().get_context_data(**kwargs)
        context['payments'] = payments
        context['edit_payment_request_forms'] = list(self.get_edit_payment_request_forms())
        return context

    def get_edit_payment_request_forms(self):
        """
        Get an iterable of EditPaymentRequestForms

        We want to instantiate each EditPaymentRequestForm with a given
        PaymentRequest.  Each subclass of this mixin defines
        .get_payment_requests_queryset() so we can change the available forms
        based on the type of user viewing (applicant or staff).
        """
        payment_requests = self.get_payment_requests_queryset().select_related('project')
        for payment_request in payment_requests:
            yield EditPaymentRequestForm(instance=payment_request)

    def get_totals(self, project):
        def percentage(total, value):
            unrounded_total = (value / total) * 100

            # round using Decimal since we're dealing with currency
            rounded_total = unrounded_total.quantize(
                decimal.Decimal('1'),
                rounding=decimal.ROUND_DOWN,
            )

            return rounded_total

        unpaid_requests = project.payment_requests.filter(Q(status=SUBMITTED) | Q(status=UNDER_REVIEW))
        awaiting_absolute = sum(unpaid_requests.values_list('value', flat=True))
        awaiting_percentage = percentage(project.value, awaiting_absolute)

        paid_requests = project.payment_requests.filter(status=PAID)
        paid_absolute = sum(paid_requests.values_list('value', flat=True))
        paid_percentage = percentage(project.value, paid_absolute)

        return {
            'awaiting_absolute': awaiting_absolute,
            'awaiting_percentage': awaiting_percentage,
            'paid_absolute': paid_absolute,
            'paid_percentage': paid_percentage,
        }


class SubmissionFilesMixin:
    """
    Mixin to provide an instantiated SelectDocumentForm
    """
    def get_context_data(self, **kwargs):
        project = self.get_object()

        files = get_files(project)

        context = super().get_context_data(**kwargs)
        context['select_document_form'] = SelectDocumentForm(files, project)
        return context


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
class ChangePaymentRequestStatusView(UpdateView):
    form_class = ChangePaymentRequestStatusForm
    model = PaymentRequest
    pk_url_kwarg = 'payment_request_id'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        for error in form.errors:
            messages.error(self.request, error)

        return redirect(self.project)

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_PAYMENT_REQUEST_STATUS,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

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

        project.send_to_compliance(self.request)

        project.is_locked = False
        project.status = CONTRACTING
        project.save(update_fields=['is_locked', 'status'])

        return response


class DeletePaymentRequestView(DeleteView):
    model = PaymentRequest
    pk_url_kwarg = 'payment_request_id'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])

        self.object = self.get_object()
        if not self.object.user_can_delete(request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic()
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)

        messenger(
            MESSAGES.DELETE_PAYMENT_REQUEST,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


class EditPaymentRequestView(UpdateView):
    form_class = EditPaymentRequestForm
    model = PaymentRequest
    pk_url_kwarg = 'payment_request_id'

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])

        is_admin = request.user.is_apply_staff
        is_owner = request.user == self.project.user
        if not (is_owner or is_admin):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request, form.errors)
        return redirect(self.project)

    def form_valid(self, form):
        response = super().form_valid(form)

        messenger(
            MESSAGES.UPDATE_PAYMENT_REQUEST,
            request=self.request,
            user=self.request.user,
            source=self.project,
            related=self.object,
        )

        return response

    def get_success_url(self):
        return self.project.get_absolute_url()


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


class RequestPaymentView(DelegatedViewMixin, CreateView):
    context_name = 'request_payment_form'
    form_class = RequestPaymentForm
    model = PaymentRequest

    def form_valid(self, form):
        project = self.kwargs['object']

        form.instance.by = self.request.user
        form.instance.project = project
        response = super().form_valid(form)

        messenger(
            MESSAGES.APPROVE_PROJECT,
            request=self.request,
            user=self.request.user,
            source=project,
        )

        return response


@method_decorator(login_required, name='dispatch')
class SelectDocumentView(SubmissionFilesMixin, FormView):
    context_name = 'select_document_form'
    form_class = SelectDocumentForm
    model = Project

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_invalid(self, form):
        for error in form.errors:
            messages.error(self.request, error)

        return redirect(self.project)

    def form_valid(self, form):
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
        kwargs['existing_files'] = get_files(self.project)
        kwargs['project'] = self.project
        return kwargs

    def get_success_url(self):
        return self.project.get_absolute_url()


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


class AdminProjectDetailView(
    ActivityContextMixin,
    DelegateableView,
    ContractsMixin,
    PaymentsMixin,
    SubmissionFilesMixin,
    DetailView,
):
    form_views = [
        CommentFormView,
        CreateApprovalView,
        RejectionView,
        RemoveDocumentView,
        RequestPaymentView,
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
        context['change_payment_request_status_forms'] = list(self.get_change_payment_request_status_forms())
        context['remaining_document_categories'] = list(self.object.get_missing_document_categories())
        return context

    def get_change_payment_request_status_forms(self):
        """
        Get an iterable of ChangePaymentRequestStatusForms

        We want to filter the available options based on the current
        PaymentRequest object so we need to initialise those forms outside of
        the template.
        """
        for payment_request in self.object.payment_requests.exclude(status=DECLINED).select_related('project'):
            yield ChangePaymentRequestStatusForm(instance=payment_request)

    def get_payment_requests_queryset(self):
        return self.object.payment_requests.filter(status=SUBMITTED)


class ApplicantProjectDetailView(ActivityContextMixin, DelegateableView, ContractsMixin, PaymentsMixin, DetailView):
    form_views = [
        CommentFormView,
        RequestPaymentView,
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

    def get_payment_requests_queryset(self):
        return self.object.payment_requests.filter(status__in=[SUBMITTED, CHANGES_REQUESTED])


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


class ProjectDetailView(ViewDispatcher):
    admin_view = AdminProjectDetailView
    applicant_view = ApplicantProjectDetailView


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
