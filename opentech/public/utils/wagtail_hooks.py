from wagtail.contrib.modeladmin.helpers import PermissionHelper
from wagtail.contrib.modeladmin.options import ModelAdminGroup, ModelAdmin, modeladmin_register

from opentech.apply.funds.models import ScreeningStatus
from opentech.public.news.models import NewsType
from opentech.public.people.models import PersonType


class NewsTypeModelAdmin(ModelAdmin):
    model = NewsType
    menu_icon = 'tag'


class PersonTypeModelAdmin(ModelAdmin):
    model = PersonType
    menu_icon = 'tag'


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


class ScreeningStatusModelAdmin(ModelAdmin):
    model = ScreeningStatus
    menu_icon = 'tag'
    permission_helper_class = ScreeningStatusPermissionHelper


class TaxonomiesModelAdminGroup(ModelAdminGroup):
    menu_label = "Taxonomies"
    items = (NewsTypeModelAdmin, PersonTypeModelAdmin, ScreeningStatusModelAdmin)
    menu_icon = 'tag'


modeladmin_register(TaxonomiesModelAdminGroup)
