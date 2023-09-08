from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from hypha.apply.utils.admin import ListRelatedMixin
from hypha.core.wagtail.admin import SettingModelAdmin

from .admin_views import (
    CreateProjectApprovalFormView,
    CreateProjectSOWFormView,
    EditProjectApprovalFormView,
    EditProjectSOWFormView,
)
from .models import (
    ContractDocumentCategory,
    DocumentCategory,
    ProjectApprovalForm,
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


class ProjectApprovalFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ProjectApprovalForm
    menu_label = "Approval Forms"
    menu_icon = "form"
    list_display = (
        "name",
        "used_by",
    )
    create_view_class = CreateProjectApprovalFormView
    edit_view_class = EditProjectApprovalFormView

    related_models = [
        ("applicationbaseprojectapprovalform", "application"),
        ("labbaseprojectapprovalform", "lab"),
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


class ProjectSettingsAdmin(SettingModelAdmin):
    model = ProjectSettings


class VendorFormSettingsAdmin(SettingModelAdmin):
    model = VendorFormSettings


class ProjectAdminGroup(ModelAdminGroup):
    menu_label = "Projects"
    menu_icon = "duplicate"
    items = (
        ContractDocumentCategoryAdmin,
        DocumentCategoryAdmin,
        ProjectApprovalFormAdmin,
        ProjectSOWFormAdmin,
        VendorFormSettingsAdmin,
        ProjectSettingsAdmin,
    )
