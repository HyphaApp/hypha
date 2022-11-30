from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from wagtail.contrib.modeladmin.helpers import PagePermissionHelper, PermissionHelper
from wagtail.contrib.modeladmin.options import WagtailRegisterable
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import SettingMenuItem
from wagtail.models import Page


class SettingModelAdmin(WagtailRegisterable):
    """
    The core SettingModelAdmin class. It has minimal implementation that allows
    adding a SettingModelAdmin class just like ModelAdmin to the ModelGroupAdmin
    as an item.

    The BaseSiteSetting still needs to be registered with `@register_setting` decorator
    and will show up in the setting menu.
    """

    model = None
    inspect_view_enabled = False
    permission_helper_class = None

    def __init__(self, parent=None):
        """
        Don't allow initialization unless self.model is set to a valid model
        """
        if not self.model or not issubclass(self.model, BaseSiteSetting):
            raise ImproperlyConfigured(
                "The model attribute on your '%s' class must be set, and "
                "must be inherit BaseSiteSetting class." % self.__class__.__name__
            )
        self.parent = parent

        self.is_pagemodel = issubclass(self.model, Page)
        self.permission_helper = self.get_permission_helper_class()(
            self.model, self.inspect_view_enabled
        )

    def get_menu_item(self, order=None):
        return SettingMenuItem(self.model)

    def get_admin_urls_for_registration(self):
        return ()

    def get_permission_helper_class(self):
        """
        Returns a permission_helper class to help with permission-based logic
        for the given model.

        **Copied from the wagtail's ModelAdmin**
        """
        if self.permission_helper_class:
            return self.permission_helper_class
        if self.is_pagemodel:
            return PagePermissionHelper
        return PermissionHelper

    def get_permissions_for_registration(self):
        """
        Utilised by Wagtail's 'register_permissions' hook to allow permissions
        for a model to be assigned to groups in settings. This is only required
        if the model isn't a Page model, and isn't registered as a Snippet

        **Copied from the wagtail's ModelAdmin**
        """
        from wagtail.snippets.models import SNIPPET_MODELS

        if not self.is_pagemodel and self.model not in SNIPPET_MODELS:
            return self.permission_helper.get_all_model_permissions()
        return Permission.objects.none()
