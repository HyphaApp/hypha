from django.urls import reverse
from django.utils.text import mark_safe

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup
from wagtail.contrib.modeladmin.helpers import PageButtonHelper

from .models import ApplicationForm, FundType, Round
from opentech.apply.categories.admin import CategoryAdmin


class ButtonsWithPreview(PageButtonHelper):
    def preview_button(self, obj, classnames_add, classnames_exclude):
        classnames = self.copy_button_classnames + classnames_add
        cn = self.finalise_classname(classnames, classnames_exclude)
        return {
            'url': reverse('wagtailadmin_pages:view_draft', args=(obj.id,)),
            'label': 'Preview',
            'classname': cn,
            'title': 'Preview this %s' % self.verbose_name,
        }

    def get_buttons_for_obj(self, obj, exclude=list(), classnames_add=list(),
                            classnames_exclude=list()):
        btns = super().get_buttons_for_obj(obj, exclude, classnames_add, classnames_exclude)

        # Put preview before delete
        btns.insert(-1, self.preview_button(obj, classnames_add, classnames_exclude))

        return btns


class RoundAdmin(ModelAdmin):
    model = Round
    menu_icon = 'doc-empty'
    list_display = ('title', 'fund', 'start_date', 'end_date')
    button_helper_class = ButtonsWithPreview

    def fund(self, obj):
        return obj.get_parent()


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
