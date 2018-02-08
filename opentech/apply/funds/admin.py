from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from .admin_helpers import (
    ButtonsWithPreview,
    FormsFundRoundListFilter,
    RoundFundChooserView,
)
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
    list_display = ('name', 'funds', 'rounds', 'labs')
    list_filter = (FormsFundRoundListFilter,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        related = [f'{field}form_set__{field}' for field in ['fund', 'round', 'lab']]
        return qs.prefetch_related(*related)

    def _list_related(self, obj, field):
        return ', '.join(getattr(obj, f'{field}form_set').values_list(f'{field}__title', flat=True))

    def funds(self, obj):
        return self._list_related(obj, 'fund')

    def labs(self, obj):
        return self._list_related(obj, 'lab')

    def rounds(self, obj):
        return self._list_related(obj, 'round')


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (RoundAdmin, FundAdmin, LabAdmin, ApplicationFormAdmin, CategoryAdmin)
