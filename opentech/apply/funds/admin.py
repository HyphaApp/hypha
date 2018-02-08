from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .admin_helpers import ButtonsWithPreview, RoundFundChooserView
from .models import ApplicationForm, FundType, LabType, Round
from opentech.apply.categories.admin import CategoryAdmin


class RoundAdmin(ModelAdmin):
    model = Round
    menu_icon = 'repeat'
    choose_parent_view_class = RoundFundChooserView
    choose_parent_template_name = 'funds/admin/parent_chooser.html'
    list_display = ('title', 'fund', 'start_date', 'end_date')
    button_helper_class = ButtonsWithPreview

    def fund(self, obj):
        return obj.get_parent()


class FundAdmin(ModelAdmin):
    model = FundType
    menu_icon = 'doc-empty'
    menu_label = 'Funds'


class LabAdmin(ModelAdmin):
    model = LabType
    menu_icon = 'doc-empty'
    menu_label = 'Labs'


class ApplicationFormAdmin(ModelAdmin):
    model = ApplicationForm
    menu_icon = 'form'


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (RoundAdmin, FundAdmin, LabAdmin, ApplicationFormAdmin, CategoryAdmin)
