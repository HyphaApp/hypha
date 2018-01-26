from django import forms
from django.urls import reverse
from django.utils.translation import ugettext as _

from wagtail.contrib.modeladmin.forms import ParentChooserForm
from wagtail.contrib.modeladmin.helpers import PageButtonHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup
from wagtail.contrib.modeladmin.views import ChooseParentView
from wagtail.wagtailcore.models import Page

from .models import ApplicationForm, FundType, Round
from opentech.apply.categories.admin import CategoryAdmin


class FundChooserForm(ParentChooserForm):
    """Changes the default chooser to be fund orientated """
    parent_page = forms.ModelChoiceField(
        label=_('Fund'),
        required=True,
        empty_label=None,
        queryset=Page.objects.none(),
        widget=forms.RadioSelect(),
    )


class RoundFundChooserView(ChooseParentView):
    def get_form(self, request):
        parents = self.permission_helper.get_valid_parent_pages(request.user)
        return FundChooserForm(parents, request.POST or None)



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
    choose_parent_view_class = RoundFundChooserView
    choose_parent_template_name = 'funds/admin/parent_chooser.html'
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
