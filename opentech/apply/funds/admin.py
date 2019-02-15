from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from opentech.apply.funds.models import ReviewerRole, ScreeningStatus
from opentech.apply.review.admin import ReviewFormAdmin
from opentech.apply.utils.admin import ListRelatedMixin
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


class ScreeningStatusPermissionHelper(PermissionHelper):
    def user_can_edit_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'change'
        a specific `self.model` instance.
        """
        return user.is_superuser

    def user_can_delete_obj(self, user, obj):
        """
        Return a boolean to indicate whether `user` is permitted to 'delete'
        a specific `self.model` instance.
        """
        return user.is_superuser


class ScreeningStatusAdmin(ModelAdmin):
    model = ScreeningStatus
    menu_icon = 'tag'
    permission_helper_class = ScreeningStatusPermissionHelper


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


class ReviewerRoleAdmin(ModelAdmin):
    model = ReviewerRole
    menu_icon = 'group'
    menu_label = 'Reviewer Roles'


class NoDeletePermission(PermissionHelper):
    def user_can_delete_obj(self, user, obj):
        return False


class ApplicationFormAdmin(ListRelatedMixin, ModelAdmin):
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


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = 'Apply'
    menu_icon = 'folder-open-inverse'
    items = (
        RoundAdmin,
        SealedRoundAdmin,
        FundAdmin,
        LabAdmin,
        RFPAdmin,
        ApplicationFormAdmin,
        ReviewFormAdmin,
        CategoryAdmin,
        ScreeningStatusAdmin,
        ReviewerRoleAdmin,
    )
