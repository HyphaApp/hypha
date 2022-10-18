from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import Menu
from wagtail.admin.wagtail_hooks import SettingsMenuItem

hypha_settings_menu = Menu(
    register_hook_name='register_hypha_settings_menu_item',
    construct_hook_name='construct_hypha_settings_menu',
)


@hooks.register('register_admin_menu_item')
def register_hypha_settings_menu():
    return SettingsMenuItem(
        _('Hypha Settings'), hypha_settings_menu, icon_name='list-ul', order=9999
    )
