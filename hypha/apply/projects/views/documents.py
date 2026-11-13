import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    CreateView,
)
from rolepermissions.checkers import has_object_permission

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.funds.models.co_applicants import CoApplicantProjectPermission
from hypha.apply.users.decorators import (
    staff_required,
)
from hypha.apply.utils.storage import PrivateMediaView

from ...funds.files import generate_private_file_path
from ..forms import (
    UploadDocumentForm,
)
from ..models.project import (
    ContractDocumentCategory,
    DocumentCategory,
    PacketFile,
    Project,
)
from ..permissions import has_permission
from .mixins import ProjectByIdMixin


class UploadDocumentView(ProjectByIdMixin, CreateView):
    form_class = UploadDocumentForm
    model = Project
    template_name = "application_projects/modals/supporting_documents_upload.html"

    def dispatch(self, request, *args, **kwargs):
        self.project = self.get_object()
        self.category = get_object_or_404(
            DocumentCategory, id=kwargs.get("category_pk")
        )
        permission = has_object_permission(
            "upload_project_documents", request.user, obj=self.project
        )
        if not permission:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        upload_document_form = self.form_class(
            instance=self.project, initial={"category": self.category}
        )
        return render(
            self.request,
            self.template_name,
            context={
                "form": upload_document_form,
                "value": _("Submit"),
                "category": self.category,
                "object": self.project,
            },
        )

    def post(self, request, *args, **kwargs):
        form = self.form_class(
            self.request.POST,
            request.FILES,
            instance=self.project,
            initial={"category": self.category},
        )
        if form.is_valid():
            form.instance.project = self.project
            form.save()
            messenger(
                MESSAGES.UPLOAD_DOCUMENT,
                request=self.request,
                user=self.request.user,
                source=self.project,
            )
            return HttpResponse(
                status=204,
                headers={
                    "HX-Trigger": json.dumps(
                        {
                            "supportingDocumentUpload": None,
                            "showMessage": _("Document has been uploaded"),
                        }
                    ),
                },
            )
        return render(
            self.request,
            self.template_name,
            context={"form": form, "value": _("Submit"), "object": self.project},
            status=400,
        )


@method_decorator(staff_required, name="dispatch")
class RemoveDocumentView(ProjectByIdMixin, View):
    model = Project

    def delete(self, *args, **kwargs):
        self.project = self.get_object()
        self.object = self.project.packet_files.get(pk=kwargs.get("document_pk"))
        self.object.delete()

        return HttpResponse(
            status=204,
            headers={
                "HX-Trigger": json.dumps(
                    {
                        "supportingDocumentRemove": None,
                        "showMessage": _("Document has been removed"),
                    }
                ),
            },
        )


@method_decorator(login_required, name="dispatch")
class ProjectPrivateMediaView(ProjectByIdMixin, UserPassesTestMixin, PrivateMediaView):
    """
    See also hypha/apply/funds/files.py
    """

    raise_exception = True

    def dispatch(self, *args, **kwargs):
        self.project = self.get_object()
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        if "file_pk" in kwargs:
            document = PacketFile.objects.get(pk=kwargs["file_pk"])
            if document.project != self.project:
                raise Http404
            return document.document
        else:
            field_id = kwargs["field_id"]
            file_name = kwargs["file_name"]
            path_to_file = generate_private_file_path(
                self.project.pk, field_id, file_name, path_start="project"
            )
            return self.storage.open(path_to_file)

    def test_func(self):
        if self.request.user.is_org_faculty:
            return True

        if self.request.user == self.project.user:
            return True

        # co-applicant with project document permission can view documents
        co_applicant = self.project.submission.co_applicants.filter(
            user=self.request.user
        ).first()
        if (
            co_applicant
            and CoApplicantProjectPermission.PROJECT_DOCUMENT
            in co_applicant.project_permission
        ):
            return True

        return False


@method_decorator(login_required, name="dispatch")
class CategoryTemplatePrivateMediaView(ProjectByIdMixin, PrivateMediaView):
    raise_exception = True

    def dispatch(self, *args, **kwargs):
        self.project = self.get_object()
        self.category_type = kwargs["type"]
        has_permission(
            "project_access",
            self.request.user,
            object=self.project,
            raise_exception=True,
        )
        return super().dispatch(*args, **kwargs)

    def get_media(self, *args, **kwargs):
        if self.category_type == "project_document":
            category = DocumentCategory.objects.get(pk=kwargs["category_pk"])
        elif self.category_type == "contract_document":
            category = ContractDocumentCategory.objects.get(pk=kwargs["category_pk"])
        else:
            raise Http404
        if not category.template:
            raise Http404
        return category.template
