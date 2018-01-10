from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .models import ApplicationForm, FundType
from opentech.apply.categories.admin import CategoryAdmin


class FundAdmin(ModelAdmin):
    model = FundType
    menu_icon = 'doc-empty'


class ApplicationFormAdmin(ModelAdmin):
    model = ApplicationForm
    menu_icon = 'form'


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (FundAdmin, ApplicationFormAdmin, CategoryAdmin)
