import datetime
import io

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.template.loader import get_template
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import (
    DetailView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

from hypha.apply.activity.messaging import MESSAGES, messenger
from hypha.apply.stream_forms.models import BaseStreamForm
from hypha.apply.todo.options import (
    PROJECT_SUBMIT_PAF,
    PROJECT_WAITING_PF,
    PROJECT_WAITING_SOW,
)
from hypha.apply.todo.views import (
    add_task_to_user,
    remove_tasks_for_user,
)
from hypha.apply.users.decorators import (
    staff_or_finance_or_contracting_required,
)
from hypha.apply.utils.models import PDFPageSettings
from hypha.apply.utils.pdfs import render_as_pdf

from ..forms import (
    ProjectForm,
    ProjectSOWForm,
)
from ..models.project import (
    Project,
    ProjectFormPointer,
)
from ..permissions import has_permission
from ..utils import (
    get_placeholder_file,
)
from .mixins import ProjectByIdMixin


@method_decorator(staff_or_finance_or_contracting_required, name="dispatch")
class ProjectSOWView(ProjectByIdMixin, DetailView):
    model = Project
    template_name_suffix = "_sow_detail"


@method_decorator(staff_or_finance_or_contracting_required, name="dispatch")
class ProjectSOWDownloadView(ProjectByIdMixin, SingleObjectMixin, View):
    model = Project

    def get(self, request, *args, **kwargs):
        export_type = kwargs.get("export_type", "pdf")
        self.object = self.get_object()
        context = {}
        context["sow_data"] = self.get_sow_data_with_field(self.object)
        context["org_name"] = settings.ORG_LONG_NAME
        context["id"] = self.object.id
        context["title"] = self.object.title
        context["project_link"] = self.request.build_absolute_uri(
            self.object.get_absolute_url()
        )
        template_path = "application_projects/sow_export.html"

        if export_type == "pdf":
            pdf_page_settings = PDFPageSettings.load(request_or_site=request)
            context["pagesize"] = pdf_page_settings.download_page_size
            context["show_footer"] = True
            return render_as_pdf(
                request=request,
                template_name=template_path,
                context=context,
                filename=self.get_slugified_file_name(export_type),
            )
        elif export_type == "docx":
            context["show_footer"] = False

            return self.render_as_docx(
                context=context,
                template=get_template(template_path),
                filename=self.get_slugified_file_name(export_type),
            )
        else:
            raise Http404(f"{export_type} type not supported at the moment")

    def render_as_docx(self, context, template, filename):
        html = template.render(context)

        buf = io.BytesIO()
        # Imported here to keep python-docx (and lxml) out of memory until needed.
        from docx import Document
        from htmldocx import HtmlToDocx

        document = Document()
        new_parser = HtmlToDocx()
        new_parser.add_html_to_document(html, document)
        document.save(buf)
        buf.seek(0)

        return FileResponse(
            buf, as_attachment=True, filename=filename, content_type="application/docx"
        )

    def get_slugified_file_name(self, export_type):
        return f"{datetime.date.today().strftime('%Y%m%d')}-{slugify(self.object.title)}.{export_type}"

    def get_sow_data_with_field(self, project):
        data_dict = {}
        if project.submission.page.specific.sow_forms.exists() and hasattr(
            project, "sow"
        ):
            form_data_dict = project.sow.form_data
            for field in project.sow.form_fields.raw_data:
                if field.get("type", None) in ["file", "multi_file"]:
                    continue
                if field["id"] in form_data_dict.keys():
                    if (
                        isinstance(field["value"], dict)
                        and "field_label" in field["value"]
                    ):
                        data_dict[field["value"]["field_label"]] = form_data_dict[
                            field["id"]
                        ]

        return data_dict


@method_decorator(staff_or_finance_or_contracting_required, name="dispatch")
class ProjectFormsEditView(BaseStreamForm, ProjectByIdMixin, UpdateView):
    model = Project

    def buttons(self):
        yield ("submit", "btn-primary", _("Save"))

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        has_permission("paf_edit", self.request.user, self.object, raise_exception=True)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        submission_attachments = []
        for _field, files in self.object.submission.extract_files().items():
            if isinstance(files, list):
                submission_attachments.extend(files)
            else:
                submission_attachments.append(files)

        return {
            "title": self.object.title,
            "buttons": self.buttons(),
            "object": self.object,
            "submissions_attachments": submission_attachments,
            **kwargs,
        }

    def get_form_class(self, form_class, draft=False, form_data=None, user=None):
        return type(
            "WagtailStreamForm",
            (form_class,),
            self.get_form_fields(draft, form_data, user),
        )


class ProjectFormEditView(ProjectFormsEditView):
    pf_form = None

    template_name = "application_projects/project_approval_form.html"

    @cached_property
    def approval_form(self):
        """Fetch the project form from the fund directly instead of going through round"""
        approval_form = self.object.submission.page.specific.approval_forms.first()

        return approval_form

    def get_pf_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class(ProjectForm)

        return form_class(**self.get_pf_form_kwargs())

    def get_pf_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.approval_form:
            fields = self.approval_form.form.get_form_fields()
        else:
            fields = {}

        kwargs["extra_fields"] = fields
        initial = self.object.raw_data
        for field_id in self.object.file_field_ids:
            initial.pop(field_id + "-uploads", False)
            initial[field_id] = get_placeholder_file(self.object.raw_data.get(field_id))
        kwargs["initial"].update(initial)
        return kwargs

    def get_pf_form_fields(self):
        return self.object.form_fields or self.approval_form.form.form_fields

    def get_context_data(self, **kwargs):
        self.pf_form = self.get_pf_form()

        submission_attachments = []
        for _field, files in self.object.submission.extract_files().items():
            if isinstance(files, list):
                submission_attachments.extend(files)
            else:
                submission_attachments.append(files)

        ctx = {
            "approval_form_exists": True if self.approval_form else False,
            "pf_form": self.pf_form,
            **super().get_context_data(),
            **kwargs,
        }

        return ctx

    def get_defined_fields(self):
        approval_form = self.approval_form
        if approval_form and not self.pf_form:
            return self.get_pf_form_fields()
        return self.object.get_defined_fields()

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """

        self.pf_form = self.get_pf_form()
        if self.pf_form.is_valid():
            try:
                pf_form_fields = self.get_pf_form_fields()
            except AttributeError:
                pf_form_fields = []

            # If the project form pointer doesn't already exist, this is a new project form
            creating = not hasattr(self.object, "pfp")

            self.pf_form.save(pf_form_fields=pf_form_fields)
            self.pf_form.delete_temporary_files()

            message = MESSAGES.EDITED_PF
            if creating:
                message = MESSAGES.CREATED_PF
                pfp = ProjectFormPointer.objects.create(project=self.object)
            else:
                pfp = self.object.pfp

            messenger(
                message,
                request=request,
                user=request.user,
                source=self.object.submission,
                related=pfp,
            )

            # remove PAF addition task for staff group
            remove_tasks_for_user(
                code=PROJECT_WAITING_PF,
                user=self.object.lead,
                related_obj=self.object,
            )
            # add project forms submission task for staff group if SOW has been updated
            # OR if the SOW doesn't exist (user_has_updated_sow_details == None)
            if (
                updated_sow := self.object.user_has_updated_sow_details
            ) or updated_sow is None:
                add_task_to_user(
                    code=PROJECT_SUBMIT_PAF,
                    user=self.object.lead,
                    related_obj=self.object,
                )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(self.pf_form)


class ProjectSOWEditView(ProjectFormEditView):
    sow_form = None

    template_name = "application_projects/project_sow_form.html"

    @cached_property
    def approval_sow_form(self):
        """Fetch the project form from the fund directly instead of going through round"""
        approval_sow_form = self.object.submission.page.specific.sow_forms.first()

        return approval_sow_form

    def get_sow_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class(ProjectSOWForm)

        return form_class(**self.get_sow_form_kwargs())

    def get_sow_form_fields(self):
        if hasattr(self.object, "sow"):
            return (
                self.object.sow.form_fields or self.approval_sow_form.form.form_fields
            )
        return self.approval_sow_form.form.form_fields

    def get_context_data(self, **kwargs):
        if self.approval_sow_form:
            self.sow_form = self.get_sow_form()

        submission_attachments = []
        for _field, files in self.object.submission.extract_files().items():
            if isinstance(files, list):
                submission_attachments.extend(files)
            else:
                submission_attachments.append(files)

        return {
            "sow_form_exists": True if self.approval_sow_form else False,
            "sow_form": self.sow_form,
            **super().get_context_data(),
            **kwargs,
        }

    def get_sow_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.approval_sow_form:
            fields = self.approval_sow_form.form.get_form_fields()

            kwargs["extra_fields"] = fields
            try:
                sow_instance = self.object.sow
                initial = sow_instance.raw_data
                for field_id in sow_instance.file_field_ids:
                    initial.pop(field_id + "-uploads", False)
                    initial[field_id] = get_placeholder_file(
                        sow_instance.raw_data.get(field_id)
                    )
                initial["project"] = self.object
                kwargs["initial"].update(initial)
            except ObjectDoesNotExist:
                kwargs["initial"].update({"project": self.object})
        return kwargs

    def get_defined_fields(self):
        if self.approval_sow_form and not self.sow_form:
            return self.get_sow_form_fields()
        return self.object.get_defined_fields()

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """

        if self.approval_sow_form:
            self.sow_form = self.get_sow_form()
            if self.sow_form.is_valid():
                try:
                    sow_form_fields = self.get_sow_form_fields()
                except AttributeError:
                    sow_form_fields = []

                creating = not hasattr(self.object, "sow")

                self.sow_form.save(sow_form_fields=sow_form_fields, project=self.object)
                self.sow_form.delete_temporary_files()

                message = MESSAGES.EDITED_SOW
                if creating:
                    message = MESSAGES.CREATED_SOW
                messenger(
                    message,
                    request=request,
                    user=request.user,
                    source=self.object.submission,
                    related=self.object.sow,
                )
                # remove SOW addition task for staff group
                remove_tasks_for_user(
                    code=PROJECT_WAITING_SOW,
                    user=self.object.lead,
                    related_obj=self.object,
                )
                # add project forms submission task for staff group if project form has been updated
                if self.object.user_has_updated_pf_details:
                    add_task_to_user(
                        code=PROJECT_SUBMIT_PAF,
                        user=self.object.lead,
                        related_obj=self.object,
                    )
                return HttpResponseRedirect(self.get_success_url())
            else:
                return self.form_invalid(self.sow_form)
