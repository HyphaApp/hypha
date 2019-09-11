from django.utils.html import mark_safe
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .models import DocumentCategory, ProjectApprovalForm


class DocumentCategoryAdmin(ModelAdmin):
    model = DocumentCategory
    menu_icon = 'doc-full'
    list_display = ('name', 'recommended_minimum',)


class ProjectApprovalFormAdmin(ModelAdmin):
    model = ProjectApprovalForm
    menu_icon = 'form'
    list_display = ('name', 'used_by',)

    def used_by(self, obj):
        rows = list()
        for field in ('funds', 'labs',):
            related = ', '.join(getattr(obj, f'{field}').values_list('title', flat=True))
            if related:
                rows.append(related)
        return mark_safe('<br>'.join(rows))


class ManageAdminGoup(ModelAdminGroup):
    menu_label = 'Manage'
    menu_icon = 'folder-open-inverse'
    items = (
        DocumentCategoryAdmin,
        ProjectApprovalFormAdmin,
    )
