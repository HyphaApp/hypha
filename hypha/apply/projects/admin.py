from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from hypha.apply.utils.admin import ListRelatedMixin

from .admin_views import CreateProjectApprovalFormView, EditProjectApprovalFormView
from .models import DocumentCategory, ProjectApprovalForm


class DocumentCategoryAdmin(ModelAdmin):
    model = DocumentCategory
    menu_icon = 'doc-full'
    list_display = ('name', 'recommended_minimum',)


class ProjectApprovalFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ProjectApprovalForm
    menu_icon = 'form'
    list_display = ('name', 'used_by',)
    create_view_class = CreateProjectApprovalFormView
    edit_view_class = EditProjectApprovalFormView

    related_models = [
        ('applicationbaseprojectapprovalform', 'application'),
        ('labbaseprojectapprovalform', 'lab'),
    ]


class ManageAdminGoup(ModelAdminGroup):
    menu_label = 'Manage'
    menu_icon = 'folder-open-inverse'
    items = (
        DocumentCategoryAdmin,
    )
