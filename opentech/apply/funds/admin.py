from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .models import ApplicationForm, FundType, Round
from opentech.apply.categories.admin import CategoryAdmin


class RoundAdmin(ModelAdmin):
    model = Round
    menu_icon = 'doc-empty'


class FundAdmin(ModelAdmin):
    model = FundType
    menu_icon = 'doc-empty'


class ApplicationFormAdmin(ModelAdmin):
    model = ApplicationForm
    menu_icon = 'form'


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (RoundAdmin, FundAdmin, ApplicationFormAdmin, CategoryAdmin)
