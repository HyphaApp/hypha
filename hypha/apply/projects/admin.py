from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .admin_views import CreateProjectApprovalFormView, EditProjectApprovalFormView
from .models import DocumentCategory, ProjectApprovalForm


class DocumentCategoryAdmin(ModelAdmin):
    model = DocumentCategory
    menu_icon = 'doc-full'
    list_display = ('name', 'recommended_minimum',)


class ProjectApprovalFormAdmin(ModelAdmin):
    model = ProjectApprovalForm
    menu_icon = 'form'
    list_display = ('name', 'used_by',)
    create_view_class = CreateProjectApprovalFormView
    edit_view_class = EditProjectApprovalFormView

    def used_by(self, obj):
        rows = list()
        for field in ('funds', 'labs',):
            related = ', '.join(getattr(obj, f'{field}').values_list('title', flat=True))
            if related:
                rows.append(related)
        return ', '.join(rows)


class ManageAdminGoup(ModelAdminGroup):
    menu_label = 'Manage'
    menu_icon = 'folder-open-inverse'
    items = (
        DocumentCategoryAdmin,
        ProjectApprovalFormAdmin,
    )
