from django.urls import reverse

from wagtail.core import hooks
from wagtail.admin.menu import MenuItem


@hooks.register('register_admin_menu_item')
def register_dashboard_menu_item():
    return MenuItem(
        'Apply Dashboard',
        reverse('dashboard:dashboard'),
        classnames='icon icon-arrow-left',
        order=100000,
    )
