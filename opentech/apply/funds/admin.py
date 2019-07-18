from django.urls import reverse
from django.utils.safestring import mark_safe
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
from opentech.apply.categories.admin import CategoryAdmin, MetaCategoryAdmin


class BaseRoundAdmin(ModelAdmin):
    choose_parent_view_class = RoundFundChooserView
    choose_parent_template_name = 'funds/admin/parent_chooser.html'
    button_helper_class = ButtonsWithPreview

    def fund(self, obj):
        return obj.get_parent()


class RoundAdmin(BaseRoundAdmin):
    model = Round
    menu_icon = 'repeat'
    list_display = ('title', 'fund', 'start_date', 'end_date', 'sealed', 'applications', 'review_forms')

    def applications(self, obj):
        def build_urls(applications):
            for application in applications:
                url = self.get_other_admin_edit_url(application.form)
                yield f'<a href="{url}">{application}</a>'

        urls = list(build_urls(obj.forms.all()))

        if not urls:
            return

        return mark_safe('<br />'.join(urls))

    def fund(self, obj):
        url = self.url_helper.get_action_url('edit', obj.fund.id)
        url_tag = f'<a href="{url}">{obj.fund}</a>'
        return mark_safe(url_tag)

    def get_other_admin_edit_url(self, obj):
        """
        Build an admin URL for the given obj.

        This builds a ModelAdmin URL for the given object, mirroring Wagtail's
        ModelAdmin.url_helper.get_action_url but works for any ModelAdmin.
        """
        app_label = obj._meta.app_label
        model_name = obj._meta.model_name
        url_name = f'{app_label}_{model_name}_modeladmin_edit'
        return reverse(url_name, args=[obj.id])

    def review_forms(self, obj):
        def build_urls(review_forms):
            for review_form in review_forms:
                url = self.get_other_admin_edit_url(review_form)
                yield f'<a href="{url}">{review_form}</a>'

        urls = list(build_urls(obj.review_forms.all()))

        if not urls:
            return

        return mark_safe('<br />'.join(urls))


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
    list_display = ('title', 'fund', 'start_date', 'end_date')


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
        MetaCategoryAdmin,
    )
