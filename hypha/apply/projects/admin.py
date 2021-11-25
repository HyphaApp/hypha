from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .models import DocumentCategory


class DocumentCategoryAdmin(ModelAdmin):
    model = DocumentCategory
    menu_icon = 'doc-full'
    list_display = ('name', 'recommended_minimum',)


class ManageAdminGoup(ModelAdminGroup):
    menu_label = 'Manage'
    menu_icon = 'folder-open-inverse'
    items = (
        DocumentCategoryAdmin,
    )
