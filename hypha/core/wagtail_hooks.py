from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import Menu
from wagtail.admin.wagtail_hooks import SettingsMenuItem

public_site_settings_menu = Menu(
    register_hook_name="register_public_site_setting_menu_item",
    construct_hook_name="construct_public_site_settings_menu",
)


@hooks.register("register_admin_menu_item")
def register_public_site_settings_menu():
    return SettingsMenuItem(
        _("Public Site"), public_site_settings_menu, icon_name="list-ul", order=9999
    )
