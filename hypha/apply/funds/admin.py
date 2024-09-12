from django.urls import re_path
from django.utils.safestring import mark_safe
from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from hypha.apply.categories.admin import CategoryAdmin, MetaTermAdmin
from hypha.apply.determinations.admin import (
    DeterminationFormAdmin,
    DeterminationFormSettingsAdmin,
    DeterminationMessageSettingsAdmin,
)
from hypha.apply.funds.models import ReviewerRole, ReviewerSettings, ScreeningStatus
from hypha.apply.review.admin import ReviewFormAdmin
from hypha.apply.utils.admin import AdminIcon, ListRelatedMixin, RelatedFormsMixin
from hypha.core.wagtail.admin.options import SettingModelAdmin

from .admin_helpers import (
    ApplicationFormButtonHelper,
    ButtonsWithPreview,
    FormsFundRoundListFilter,
    RoundAdminURLHelper,
    RoundFundChooserView,
    RoundStateListFilter,
)
from .admin_views import (
    CopyApplicationFormViewClass,
    CreateApplicationFormView,
    EditApplicationFormView,
)
from .models import (
    ApplicationForm,
    ApplicationSettings,
    FundType,
    LabType,
    RequestForPartners,
    Round,
    SealedRound,
)


class BaseRoundAdmin(ModelAdmin):
    choose_parent_view_class = RoundFundChooserView
    choose_parent_template_name = "funds/admin/parent_chooser.html"
    button_helper_class = ButtonsWithPreview

    def fund(self, obj):
        return obj.get_parent()


class RoundAdmin(BaseRoundAdmin, RelatedFormsMixin):
    model = Round
    menu_icon = str(AdminIcon.ROUND)
    list_display = (
        "title",
        "fund",
        "start_date",
        "end_date",
        "application_forms",
        "review_forms",
    )
    list_filter = (RoundStateListFilter,)
    url_helper_class = RoundAdminURLHelper

    def fund(self, obj):
        url = self.url_helper.get_action_url("edit", obj.fund.id)
        url_tag = f'<a href="{url}">{obj.fund}</a>'
        return mark_safe(url_tag)


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
    menu_icon = str(AdminIcon.SCREENING_STATUS)
    list_display = ("title", "yes", "default")
    permission_helper_class = ScreeningStatusPermissionHelper
    list_display = ("title", "yes", "default")


class SealedRoundAdmin(BaseRoundAdmin):
    model = SealedRound
    menu_icon = str(AdminIcon.SEALED_ROUND)
    menu_label = "Sealed Rounds"
    list_display = ("title", "fund", "start_date", "end_date")


class FundAdmin(ModelAdmin, RelatedFormsMixin):
    model = FundType
    menu_icon = str(AdminIcon.FUND)
    menu_label = "Funds"
    list_display = ("title", "application_forms", "review_forms", "determination_forms")


class RFPAdmin(ModelAdmin):
    model = RequestForPartners
    menu_icon = str(AdminIcon.REQUEST_FOR_PARTNERS)
    menu_label = "Request For Partners"


class LabAdmin(ModelAdmin, RelatedFormsMixin):
    model = LabType
    menu_icon = str(AdminIcon.LAB)
    menu_label = "Labs"
    list_display = ("title", "application_forms", "review_forms", "determination_forms")


class ReviewerRoleAdmin(ModelAdmin):
    model = ReviewerRole
    menu_icon = str(AdminIcon.REVIEWER_ROLE)
    menu_label = "Reviewer Roles"


class DeletePermission(PermissionHelper, ListRelatedMixin):
    related_models = [
        ("applicationbaseform", "application"),
        ("roundbaseform", "round"),
        ("labbaseform", "lab"),
    ]

    def user_can_delete_obj(self, user, obj):
        if str(self.used_by(obj)):
            return False
        return True


class ApplicationFormAdmin(ListRelatedMixin, ModelAdmin):
    model = ApplicationForm
    menu_icon = str(AdminIcon.APPLICATION_FORM)
    list_display = ("name", "used_by")
    list_filter = (FormsFundRoundListFilter,)
    permission_helper_class = DeletePermission
    button_helper_class = ApplicationFormButtonHelper
    create_view_class = CreateApplicationFormView
    edit_view_class = EditApplicationFormView

    related_models = [
        ("applicationbaseform", "application"),
        ("roundbaseform", "round"),
        ("labbaseform", "lab"),
    ]

    def copy_form_view(self, request, instance_pk):
        kwargs = {"model_admin": self, "form_pk": instance_pk}
        view_class = CopyApplicationFormViewClass
        return view_class.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        """Add the url for creating form copy."""
        urls = super().get_admin_urls_for_registration()
        copy_form_url = re_path(
            self.url_helper.get_action_url_pattern("copy_form"),
            self.copy_form_view,
            name=self.url_helper.get_action_url_name("copy_form"),
        )
        return urls + (copy_form_url,)


class ApplicationSettingAdmin(SettingModelAdmin):
    model = ApplicationSettings


class ReviewerSettingAdmin(SettingModelAdmin):
    model = ReviewerSettings


class ApplyAdminGroup(ModelAdminGroup):
    menu_label = "Apply"
    menu_icon = str(AdminIcon.APPLY)
    items = (
        RoundAdmin,
        SealedRoundAdmin,
        FundAdmin,
        LabAdmin,
        RFPAdmin,
        ApplicationFormAdmin,
        ApplicationSettingAdmin,
        ReviewFormAdmin,
        ReviewerSettingAdmin,
        DeterminationFormAdmin,
        DeterminationMessageSettingsAdmin,
        DeterminationFormSettingsAdmin,
        CategoryAdmin,
        ScreeningStatusAdmin,
        ReviewerRoleAdmin,
        MetaTermAdmin,
    )
