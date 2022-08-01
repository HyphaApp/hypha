from urllib.parse import urljoin

from django.urls import reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem

from hypha.apply.home.models import ApplyHomePage


@hooks.register('register_admin_menu_item')
def register_dashboard_menu_item():
    apply_home = ApplyHomePage.objects.first()
    return MenuItem(
        'Apply Dashboard',
        urljoin(apply_home.url, reverse('dashboard:dashboard', 'hypha.apply.urls')),
        classnames='icon icon-arrow-left',
        order=100000,
    )
