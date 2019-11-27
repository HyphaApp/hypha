from django.conf.urls import url
from django.urls import reverse
from django.utils.safestring import mark_safe
from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup

from opentech.apply.funds.models import ReviewerRole, ScreeningStatus
from opentech.apply.review.admin import ReviewFormAdmin
from opentech.apply.utils.admin import ListRelatedMixin
from opentech.apply.categories.admin import CategoryAdmin, MetaTermAdmin

from .admin_helpers import (
    ButtonsWithPreview,
    FormsFundRoundListFilter,
    RoundStateListFilter,
    RoundFundChooserView,
    RoundAdminURLHelper,
    ApplicationFormButtonHelper,
)
from .admin_views import CopyApplicationFormViewClass
from .models import ApplicationForm, FundType, LabType, RequestForPartners, Round, SealedRound


class BaseRoundAdmin(ModelAdmin):
    choose_parent_view_class = RoundFundChooserView
    choose_parent_template_name = 'funds/admin/parent_chooser.html'
    button_helper_class = ButtonsWithPreview

    def fund(self, obj):
        return obj.get_parent()


class RoundAdmin(BaseRoundAdmin):
    model = Round
    menu_icon = 'repeat'
    list_display = ('title', 'fund', 'start_date', 'end_date', 'applications', 'review_forms')
    list_filter = (RoundStateListFilter,)
    url_helper_class = RoundAdminURLHelper

    def applications(self, obj):

        def build_urls(applications):
            for application in applications:
                url = reverse('funds_applicationform_modeladmin_edit', args=[application.form.id])
                yield f'<a href="{url}">{application}</a>'

        urls = list(build_urls(obj.forms.all()))

        if not urls:
            return

        return mark_safe('<br />'.join(urls))

    def fund(self, obj):
        url = self.url_helper.get_action_url('edit', obj.fund.id)
        url_tag = f'<a href="{url}">{obj.fund}</a>'
        return mark_safe(url_tag)

    def review_forms(self, obj):
        def build_urls(reviews):
            for review in reviews:
                url = reverse('review_reviewform_modeladmin_edit', args=[review.form.id])
                yield f'<a href="{url}">{review}</a>'

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
    button_helper_class = ApplicationFormButtonHelper

    related_models = [
        ('applicationbaseform', 'application'),
        ('roundbaseform', 'round'),
        ('labbaseform', 'lab'),
    ]

    def copy_form_view(self, request, instance_pk):
        kwargs = {'model_admin': self, 'form_pk': instance_pk}
        view_class = CopyApplicationFormViewClass
        return view_class.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        """Add the url for creating form copy."""
        urls = super().get_admin_urls_for_registration()
        copy_form_url = url(
            self.url_helper.get_action_url_pattern('copy_form'),
            self.copy_form_view,
            name=self.url_helper.get_action_url_name('copy_form')
        )
        return urls + (copy_form_url, )


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
        MetaTermAdmin,
    )
