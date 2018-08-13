from django.utils.html import mark_safe

from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from opentech.apply.review.admin import ReviewFormAdmin
from .admin_helpers import (
    ButtonsWithPreview,
    FormsFundRoundListFilter,
    RoundFundChooserView,
)
from .models import ApplicationForm, FundType, LabType, RequestForPartners, Round, SealedRound
from opentech.apply.categories.admin import CategoryAdmin


class BaseRoundAdmin(ModelAdmin):
    choose_parent_view_class = RoundFundChooserView
    choose_parent_template_name = 'funds/admin/parent_chooser.html'
    list_display = ('title', 'fund', 'start_date', 'end_date')
    button_helper_class = ButtonsWithPreview

    def fund(self, obj):
        return obj.get_parent()


class RoundAdmin(BaseRoundAdmin):
    model = Round
    menu_icon = 'repeat'


class SealedRoundAdmin(BaseRoundAdmin):
    model = SealedRound
    menu_icon = 'locked'
    menu_label = 'Sealed Rounds'


class FundAdmin(ModelAdmin):
    model = FundType
    menu_icon = 'doc-empty'
    menu_label = 'Funds'


class RFPAdmin(ModelAdmin):
    model = RequestForPartners
    menu_icon = 'group'
    menu_label = 'Request For Partners'


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

    related_models = [
        ('applicationbaseform', 'application'),
        ('roundbaseform', 'round'),
        ('labbaseform', 'lab'),
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        related = [f'{form}_set__{field}' for form, field in self.related_models]
        return qs.prefetch_related(*related)

    def _list_related(self, obj, form, field):
        return ', '.join(getattr(obj, f'{form}_set').values_list(f'{field}__title', flat=True))

    def used_by(self, obj):
        rows = list()
        for form, field in self.related_models:
            related = self._list_related(obj, form, field)
            if related:
                rows.append(related)
        return mark_safe('<br>'.join(rows))


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (RoundAdmin, SealedRoundAdmin, FundAdmin, LabAdmin, RFPAdmin, ApplicationFormAdmin, ReviewFormAdmin, CategoryAdmin)
