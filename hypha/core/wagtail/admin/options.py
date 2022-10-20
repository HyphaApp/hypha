from django.core.exceptions import ImproperlyConfigured
from wagtail.contrib.modeladmin.options import WagtailRegisterable
from wagtail.contrib.settings.models import BaseSetting
from wagtail.contrib.settings.registry import SettingMenuItem


class SettingModelAdmin(WagtailRegisterable):
    """
    The core SettingModelAdmin class. It has minimal implementation that allows
    adding a SettingModelAdmin class just like ModelAdmin to the ModelGroupAdmin
    as an item.

    The BaseSetting still needs to be registered with `@register_setting` decorator
    and will show up in the setting menu.
    """

    model = None

    def __init__(self, parent=None):
        """
        Don't allow initialization unless self.model is set to a valid model
        """
        if not self.model or not issubclass(self.model, BaseSetting):
            raise ImproperlyConfigured(
                "The model attribute on your '%s' class must be set, and "
                "must be inherit BaseSetting class." % self.__class__.__name__
            )
        self.parent = parent

    def get_menu_item(self, order=None):
        return SettingMenuItem(self.model)

    def get_admin_urls_for_registration(self):
        return ()
