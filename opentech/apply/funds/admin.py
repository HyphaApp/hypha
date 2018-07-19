from django.utils.html import mark_safe

from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from opentech.apply.review.models import ReviewForm
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


class NoDeletePermission(PermissionHelper):
    def user_can_delete_obj(self, user, obj):
        return False


class ApplicationFormAdmin(ModelAdmin):
    model = ApplicationForm
    menu_icon = 'form'
    list_display = ('name', 'used_by')
    list_filter = (FormsFundRoundListFilter,)
    permission_helper_class = NoDeletePermission

    related_models = ['fund', 'lab', 'round']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        related = [f'{field}form_set__{field}' for field in self.related_models]
        return qs.prefetch_related(*related)

    def _list_related(self, obj, field):
        return ', '.join(getattr(obj, f'{field}form_set').values_list(f'{field}__title', flat=True))

    def used_by(self, obj):
        rows = list()
        for model in self.related_models:
            related = self._list_related(obj, model)
            if related:
                rows.append(model.title() + ': ' + related)
        return mark_safe('<br>'.join(rows))


class ReviewFormAdmin(ModelAdmin):
    model = ReviewForm
    menu_icon = 'form'


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (RoundAdmin, FundAdmin, LabAdmin, ApplicationFormAdmin, ReviewFormAdmin, CategoryAdmin)
