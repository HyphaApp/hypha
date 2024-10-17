from django.urls import reverse
from django.utils.translation import gettext as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem


@hooks.register("register_admin_menu_item")
def register_dashboard_menu_item():
    return MenuItem(
        _("Goto Dashboard"),
        reverse("dashboard:dashboard"),
        classname="icon icon-arrow-left",
        order=100000,
    )
