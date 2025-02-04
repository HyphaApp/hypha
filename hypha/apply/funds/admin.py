from django.urls import reverse
from django.utils.safestring import mark_safe
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import (
    ModelAdmin,
    ModelAdminGroup,
    modeladmin_register,
)
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from hypha.apply.categories.admin import CategoryAdmin, MetaTermAdmin
from hypha.apply.determinations.admin import (
    DeterminationFormAdmin,
    DeterminationFormSettingsAdmin,
    DeterminationMessageSettingsAdmin,
)
from hypha.apply.funds.models import ReviewerRole, ReviewerSettings, ScreeningStatus
from hypha.apply.review.admin import ReviewFormAdmin
from hypha.apply.utils.admin import AdminIcon, RelatedFormsMixin
from hypha.core.wagtail.admin.options import SettingModelAdmin

from .admin_helpers import (
    ButtonsWithPreview,
    RoundAdminURLHelper,
    RoundFundChooserView,
    RoundStateListFilter,
)
from .models import (
    ApplicationForm,
    ApplicationSettings,
    RequestForPartners,
    Round,
    SealedRound,
)


class ScreeningStatusAdmin(SnippetViewSet):
    model = ScreeningStatus
    icon = str(AdminIcon.SCREENING_STATUS)
    list_display = ("title", "yes", "default")

    def user_can_edit(self, user):
        return user.is_superuser

    def user_can_delete(self, user):
        return user.is_superuser


class ReviewerRoleAdmin(SnippetViewSet):
    model = ReviewerRole
    icon = str(AdminIcon.REVIEWER_ROLE)
    menu_label = "Reviewer Roles"


# having issues with Locale during save
# class FundAdmin(SnippetViewSet, RelatedFormsMixin):
#     model = FundType
#     icon = str(AdminIcon.FUND)
#     menu_label = "Funds"
#     list_display = ("title", "application_forms", "get_review_forms", "get_determination_forms")
#
#
# class LabAdmin(SnippetViewSet, RelatedFormsMixin):
#     model = LabType
#     icon = str(AdminIcon.LAB)
#     menu_label = "Labs"
#     list_display = ("title", "application_forms", "get_review_forms", "get_determination_forms")


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


class SealedRoundAdmin(BaseRoundAdmin):
    model = SealedRound
    menu_icon = str(AdminIcon.SEALED_ROUND)
    menu_label = "Sealed Rounds"
    list_display = ("title", "fund", "start_date", "end_date")


# class FundAdmin(ModelAdmin, RelatedFormsMixin):
#     model = FundType
#     menu_icon = str(AdminIcon.FUND)
#     menu_label = "Funds"
#     list_display = ("title", "application_forms", "review_forms", "determination_forms")
#
#
class RFPAdmin(ModelAdmin):
    model = RequestForPartners
    menu_icon = str(AdminIcon.REQUEST_FOR_PARTNERS)
    menu_label = "Request For Partners"


#
# class LabAdmin(ModelAdmin, RelatedFormsMixin):
#     model = LabType
#     menu_icon = str(AdminIcon.LAB)
#     menu_label = "Labs"
#     list_display = ("title", "application_forms", "review_forms", "determination_forms")
#


class ApplicationFormAdmin(SnippetViewSet):
    model = ApplicationForm
    menu_icon = str(AdminIcon.APPLICATION_FORM)
    list_display = ("name", "used_by")

    def get_queryset(self, request):
        # Explicitly define the queryset for this snippet
        qs = self.model.objects.all()

        # Prefetch related fields for the 'used_by' logic
        related = [
            "applicationbaseform_set__application",
            "roundbaseform_set__round",
            "labbaseform_set__lab",
        ]
        return qs.prefetch_related(*related)


register_snippet(ApplicationFormAdmin)
register_snippet(ScreeningStatusAdmin)
register_snippet(ReviewerRoleAdmin)
# register_snippet(FundAdmin)
# register_snippet(LabAdmin)


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
        RFPAdmin,
        ApplicationSettingAdmin,
        ReviewFormAdmin,
        ReviewerSettingAdmin,
        DeterminationFormAdmin,
        DeterminationMessageSettingsAdmin,
        DeterminationFormSettingsAdmin,
        CategoryAdmin,
        MetaTermAdmin,
    )

    def get_submenu_items(self):
        # Get existing items
        submenu_items = super().get_submenu_items()

        snippets = [
            {
                "model": ReviewerRole,
                "menu_label": "Reviewer Roles",
                "icon_name": str(AdminIcon.REVIEWER_ROLE),
            },
            # {"model": FundType, "menu_label": "Funds", "icon_name": str(AdminIcon.FUND)},
            # {"model": LabType, "menu_label": "Labs", "icon_name": str(AdminIcon.LAB)},
            # {"model": RequestForPartners, "menu_label": "Request For Partners", "icon_name": str(AdminIcon.REQUEST_FOR_PARTNERS)},
            {
                "model": ScreeningStatus,
                "menu_label": "Screening Decisions",
                "icon_name": str(AdminIcon.SCREENING_STATUS),
            },
            {
                "model": ApplicationForm,
                "menu_label": "Application Forms",
                "icon_name": str(AdminIcon.APPLICATION_FORM),
            },
        ]

        for snippet in snippets:
            snippet_url = reverse(
                f"wagtailsnippets_{snippet['model']._meta.app_label}_{snippet['model']._meta.model_name}:list",
            )
            submenu_items.append(
                MenuItem(
                    snippet["menu_label"],
                    snippet_url,
                    icon_name=snippet["icon_name"],
                )
            )

        return submenu_items


modeladmin_register(ApplyAdminGroup)
