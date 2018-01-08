from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .models import ApplicationForm, Category, FundType


class FundAdmin(ModelAdmin):
    model = FundType
    menu_icon = 'doc-empty'


class CategoryAdmin(ModelAdmin):
    menu_label = 'Category Questions'
    menu_icon = 'list-ul'
    model = Category


class ApplicationFormAdmin(ModelAdmin):
    model = ApplicationForm
    menu_icon = 'form'


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (FundAdmin, ApplicationFormAdmin, CategoryAdmin)
