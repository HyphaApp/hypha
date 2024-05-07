from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from hypha.apply.utils.admin import ListRelatedMixin
from hypha.core.wagtail.admin import SettingModelAdmin

from .admin_views import (
    CreateProjectFormView,
    CreateProjectReportFormView,
    CreateProjectSOWFormView,
    EditProjectFormView,
    EditProjectReportFormView,
    EditProjectSOWFormView,
)
from .models import (
    ContractDocumentCategory,
    DocumentCategory,
    ProjectForm,
    ProjectReportForm,
    ProjectSettings,
    ProjectSOWForm,
    VendorFormSettings,
)


class DocumentCategoryAdmin(ModelAdmin):
    model = DocumentCategory
    menu_icon = "doc-full"
    list_display = (
        "name",
        "required",
    )


class ContractDocumentCategoryAdmin(ModelAdmin):
    model = ContractDocumentCategory
    menu_icon = "doc-full"
    list_display = (
        "name",
        "required",
    )


class ProjectFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ProjectForm
    menu_label = "Project Forms"
    menu_icon = "form"
    list_display = (
        "name",
        "used_by",
    )
    create_view_class = CreateProjectFormView
    edit_view_class = EditProjectFormView

    related_models = [
        ("applicationbaseprojectform", "application"),
        ("labbaseprojectform", "lab"),
    ]


class ProjectSOWFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ProjectSOWForm
    menu_label = "SOW Forms"
    menu_icon = "form"
    list_display = (
        "name",
        "used_by",
    )
    create_view_class = CreateProjectSOWFormView
    edit_view_class = EditProjectSOWFormView

    related_models = [
        ("applicationbaseprojectsowform", "application"),
        ("labbaseprojectsowform", "lab"),
    ]


class ProjectReportFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ProjectReportForm
    menu_label = "Report Forms"
    menu_icon = "form"
    list_display = (
        "name",
        "used_by",
    )
    create_view_class = CreateProjectReportFormView
    edit_view_class = EditProjectReportFormView

    related_models = [
        ("applicationbaseprojectreportform", "application"),
        ("labbaseprojectreportform", "lab"),
    ]


class ProjectSettingsAdmin(SettingModelAdmin):
    model = ProjectSettings


class VendorFormSettingsAdmin(SettingModelAdmin):
    model = VendorFormSettings


class ProjectAdminGroup(ModelAdminGroup):
    menu_label = "Projects"
    menu_icon = "folder-open-1"
    items = (
        ContractDocumentCategoryAdmin,
        DocumentCategoryAdmin,
        ProjectFormAdmin,
        ProjectReportFormAdmin,
        ProjectSOWFormAdmin,
        VendorFormSettingsAdmin,
        ProjectSettingsAdmin,
    )
