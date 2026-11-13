import datetime
import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django_htmx.http import (
    HttpResponseClientRefresh,
)
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models.co_applicants import CoApplicantProjectPermission
from hypha.apply.todo.options import (
    PROJECT_WAITING_CONTRACT,
    PROJECT_WAITING_CONTRACT_DOCUMENT,
    PROJECT_WAITING_CONTRACT_REVIEW,
    PROJECT_WAITING_INVOICE,
)
from hypha.apply.todo.views import (
    add_task_to_user,
    remove_tasks_for_user,
    remove_tasks_for_user_group,
)
from hypha.apply.users.decorators import (
    staff_required,
)
from hypha.apply.users.roles import CONTRACTING_GROUP_NAME
from hypha.apply.utils.storage import PrivateMediaView

from ..forms import (
    ApproveContractForm,
    SubmitContractDocumentsForm,
    UploadContractDocumentForm,
    UploadContractForm,
)
from ..models.project import (
    CONTRACTING,
    INVOICING_AND_REPORTING,
    Contract,
    ContractDocumentCategory,
    ContractPacketFile,
    Project,
)
from ..permissions import has_permission
from .mixins import ProjectByIdMixin


@method_decorator(login_required, name="dispatch")
class RemoveContractDocumentView(ProjectByIdMixin, View):
    model = Project

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()

        permission = has_object_permission(
            "update_contracting_documents", request.user, obj=self.project
        )
        if not permission:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def delete(self, *args, **kwargs):
        document = self.project.contract_packet_files.get(pk=kwargs.get("document_pk"))
        document.delete()

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "contractingDocumentRemove": None,
                        "showMessage": _("Contracting document has been removed"),
                    }
                ),
            },
        )


# GENERAL FORM VIEWS


@method_decorator(staff_required, name="dispatch")
class ApproveContractView(ProjectByIdMixin, View):
    form_class = ApproveContractForm
    model = Contract
    template_name = "application_projects/modals/approve_contract.html"

    def get_contract_object(self):
        latest_contract = self.project.contracts.order_by("-created_at").first()
        if latest_contract and not latest_contract.approver:
            return latest_contract

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        self.object = self.get_contract_object()
        # permission
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.object
        kwargs.pop("user")
        return kwargs

    def get(self, *args, **kwargs):
        form = self.form_class(instance=self.object)
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Confirm"),
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST, instance=self.object)
        if form.is_valid():
            with transaction.atomic():
                form.instance.approver = self.request.user
                form.instance.approved_at = timezone.now()
                form.instance.project = self.project
                form.save()

                old_stage = self.project.status

                messenger(
                    MESSAGES.APPROVE_CONTRACT,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                    related=self.object,
                )
                # remove Project waiting contract review task for staff
                remove_tasks_for_user(
                    code=PROJECT_WAITING_CONTRACT_REVIEW,
                    user=self.project.lead,
                    related_obj=self.project,
                )

                self.project.status = INVOICING_AND_REPORTING
                self.project.save(update_fields=["status"])

                messenger(
                    MESSAGES.PROJECT_TRANSITION,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                    related=old_stage,
                )
                # add Project waiting invoice task for applicant
                add_task_to_user(
                    code=PROJECT_WAITING_INVOICE,
                    user=self.project.user,
                    related_obj=self.project,
                )

            messages.success(
                self.request,
                _(
                    "Contractor documents have been approved.  You can receive invoices from vendor now."
                ),
            )
            return HttpResponseClientRefresh()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Confirm"),
                "object": self.project,
            },
        )


@method_decorator(login_required, name="dispatch")
class UploadContractView(ProjectByIdMixin, View):
    model = Project
    form_class = UploadContractForm
    template_name = "application_projects/modals/upload_contract.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        has_permission(
            "contract_upload", request.user, object=self.project, raise_exception=True
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.get_form()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "user": self.request.user,
                "value": _("Upload") if self.request.user.is_applicant else _("Submit"),
                "object": self.project,
            },
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance")
        kwargs.pop("user")
        return kwargs

    def get_form(self, *args, **kwargs):
        form = self.form_class(*args, **kwargs)
        if self.request.user.is_applicant:
            form.fields.pop("signed_and_approved")
        return form

    def post(self, *args, **kwargs):
        form = self.get_form(self.request.POST)

        if form.is_valid():
            if self.project.contracts.exists():
                form.instance = self.project.contracts.order_by("created_at").first()

            form.instance.project = self.project

            if self.request.user.is_applicant:
                form.instance.signed_by_applicant = True
                form.instance.uploaded_by_applicant_at = timezone.now()
                messages.success(self.request, _("Countersigned contract uploaded"))
            elif self.request.user.is_contracting or self.request.user.is_apply_staff:
                form.instance.uploaded_by_contractor_at = timezone.now()
                messages.success(self.request, _("Signed contract uploaded"))

            form.save()

            contract_signed_and_approved = form.cleaned_data.get("signed_and_approved")
            if contract_signed_and_approved:
                form.instance.approver = self.request.user
                form.instance.approved_at = timezone.now()
                form.instance.signed_and_approved = contract_signed_and_approved
                form.instance.signed_by_applicant = True
                form.instance.save(
                    update_fields=[
                        "approver",
                        "approved_at",
                        "signed_and_approved",
                        "signed_by_applicant",
                    ]
                )

                self.project.status = INVOICING_AND_REPORTING
                self.project.save(update_fields=["status"])
                old_stage = CONTRACTING

                if settings.PROJECTS_START_AFTER_CONTRACTING:
                    self.project.proposed_start = datetime.date.today()
                    self.project.save()

                messenger(
                    MESSAGES.PROJECT_TRANSITION,
                    request=self.request,
                    user=self.request.user,
                    source=self.project,
                    related=old_stage,
                )
                # remove Project waiting contract task for contracting/staff group
                if settings.STAFF_UPLOAD_CONTRACT:
                    remove_tasks_for_user(
                        code=PROJECT_WAITING_CONTRACT,
                        user=self.project.lead,
                        related_obj=self.project,
                    )
                else:
                    remove_tasks_for_user_group(
                        code=PROJECT_WAITING_CONTRACT,
                        user_group=Group.objects.filter(name=CONTRACTING_GROUP_NAME),
                        related_obj=self.project,
                    )
                # add Project waiting invoice task for applicant
                add_task_to_user(
                    code=PROJECT_WAITING_INVOICE,
                    user=self.project.user,
                    related_obj=self.project,
                )
            else:
                if self.request.user != self.project.user:
                    messenger(
                        MESSAGES.UPLOAD_CONTRACT,
                        request=self.request,
                        user=self.request.user,
                        source=self.project,
                        related=form.instance,
                    )
                    # remove Project waiting contract task for contracting/staff group
                    if settings.STAFF_UPLOAD_CONTRACT:
                        remove_tasks_for_user(
                            code=PROJECT_WAITING_CONTRACT,
                            user=self.project.lead,
                            related_obj=self.project,
                        )
                    else:
                        remove_tasks_for_user_group(
                            code=PROJECT_WAITING_CONTRACT,
                            user_group=Group.objects.filter(
                                name=CONTRACTING_GROUP_NAME
                            ),
                            related_obj=self.project,
                        )
                    # add Project waiting contract document task for applicant
                    add_task_to_user(
                        code=PROJECT_WAITING_CONTRACT_DOCUMENT,
                        user=self.project.user,
                        related_obj=self.project,
                    )
            return HttpResponseClientRefresh()

        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "user": self.request.user,
                "value": _("Upload") if self.request.user.is_applicant else _("Submit"),
                "object": self.project,
            },
        )


@method_decorator(login_required, name="dispatch")
class SubmitContractDocumentsView(View):
    model = Project
    form_class = SubmitContractDocumentsForm
    template_name = "application_projects/modals/submit_contracting_documents.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=kwargs.get("pk"))
        if ContractDocumentCategory.objects.filter(
            ~Q(contract_packet_files__project=self.project) & Q(required=True)
        ).exists():
            raise PermissionDenied
        contract = self.project.contracts.order_by("-created_at").first()
        has_permission(
            "submit_contract_documents",
            request.user,
            object=self.project,
            raise_exception=True,
            contract=contract,
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        form = self.form_class()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        form = self.form_class(self.request.POST, instance=self.project)
        if form.is_valid():
            form.save()

            self.project.submitted_contract_documents = True
            self.project.save(update_fields=["submitted_contract_documents"])

            messenger(
                MESSAGES.SUBMIT_CONTRACT_DOCUMENTS,
                request=self.request,
                user=self.request.user,
                source=self.project,
            )
            # remove project waiting contract documents task for applicant
            remove_tasks_for_user(
                code=PROJECT_WAITING_CONTRACT_DOCUMENT,
                user=self.project.user,
                related_obj=self.project,
            )
            # add project waiting contract review task for staff
            add_task_to_user(
                code=PROJECT_WAITING_CONTRACT_REVIEW,
                user=self.project.lead,
                related_obj=self.project,
            )

            messages.success(self.request, _("Contract documents submitted"))
            return HttpResponseClientRefresh()
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "object": self.project,
            },
        )


@method_decorator(login_required, name="dispatch")
class UploadContractDocumentView(ProjectByIdMixin, View):
    form_class = UploadContractDocumentForm
    model = Project
    context_name = "contract_document_form"
    template_name = "application_projects/modals/contracting_documents_upload.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        self.category = get_object_or_404(
            ContractDocumentCategory, id=kwargs.get("category_pk")
        )
        permission = has_object_permission(
            "update_contracting_documents", request.user, self.project
        )
        if not permission:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        upload_contract_document_form = self.form_class(
            instance=self.project, initial={"category": self.category}
        )
        return render(
            self.request,
            self.template_name,
            context={
                "form": upload_contract_document_form,
                "value": _("Submit"),
                "category": self.category,
                "object": self.project,
            },
        )

    def post(self, *args, **kwargs):
        form = self.form_class(
            self.request.POST,
            self.request.FILES,
            instance=self.project,
            initial={"category": self.category},
        )
        if form.is_valid():
            form.instance.project = self.project
            form.save()

            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "contractingDocumentUpload": None,
                            "showMessage": _("Contracting document has been uploaded"),
                        }
                    ),
                },
            )
        return render(
            self.request,
            self.template_name,
            context={
                "form": form,
                "value": _("Submit"),
                "category": self.category,
                "object": self.project,
            },
        )


# PROJECT VIEW


@method_decorator(login_required, name="dispatch")
class ContractPrivateMediaView(ProjectByIdMixin, UserPassesTestMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        self.project = self.get_object()
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        document = Contract.objects.get(pk=kwargs["file_pk"])
        if document.project != self.project:
            raise Http404
        return document.file

    def test_func(self):
        if self.request.user.is_apply_staff or self.request.user.is_contracting:
            return True

        if self.request.user == self.project.user:
            return True

        # co-applicant with contract document permission can view documents
        co_applicant = self.project.submission.co_applicants.filter(
            user=self.request.user
        ).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.CONTRACTING_DOCUMENT
            in co_applicant.project_permission
        ):
            return True

        return False


@method_decorator(login_required, name="dispatch")
class ContractDocumentPrivateMediaView(ProjectByIdMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        self.project = self.get_object()
        self.document = ContractPacketFile.objects.get(pk=kwargs["file_pk"])
        has_permission(
            "view_contract_documents",
            self.request.user,
            object=self.project,
            contract_category=self.document.category,
            raise_exception=True,
        )
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        if self.document.project != self.project:
            raise Http404
        return self.document.document


# PROJECT FORM VIEWS
