import importlib

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

DEFAULT_NAV_ITEMS = [
    {
        "title": _("My Dashboard"),
        "url": reverse_lazy("dashboard:dashboard"),
        "permission_method": "hypha.apply.users.decorators.has_dashboard_access",
    },
    {
        "title": _("Submissions"),
        # kind of basic url to figure out active tab
        "url": reverse_lazy("apply:submissions:overview"),
        "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_reviewer_required",
        "sub_items": [
            {
                "title": _("All Submissions"),
                "url": reverse_lazy("apply:submissions:list"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_reviewer_required",
            },
            {
                "title": _("Staff Assignments"),
                "url": reverse_lazy("apply:submissions:staff_assignments"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff",
            },
            {
                "title": _("Reviews"),
                "url": reverse_lazy("apply:submissions:reviewer_leaderboard"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff",
            },
            {
                "title": _("Results"),
                "url": reverse_lazy("apply:submissions:result"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff",
            },
            {
                "title": _("Staff flagged"),
                "url": reverse_lazy("apply:submissions:staff_flagged"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff",
            },
        ],
    },
    {
        "title": _("Projects"),
        # kind of basic url to figure out active tab
        "url": reverse_lazy("apply:projects:overview"),
        "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_finance_or_contracting",
        "sub_items": [
            {
                "title": _("All Projects"),
                "url": reverse_lazy("apply:projects:all"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_finance_or_contracting",
            },
            {
                "title": _("Invoices"),
                "url": reverse_lazy("apply:projects:invoices"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_finance",
            },
            {
                "title": _("Reports"),
                "url": reverse_lazy("apply:projects:reports:all"),
                "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_finance",
            },
        ],
    },
]


def resolve_and_check_permission(user, method: str) -> bool:
    """Resolve the method path and check if the user has permission.

    Args:
        user: user object
        method: import path to the method to check permission

    Returns:
        bool: True if user has permission, False otherwise
    """
    module = importlib.import_module(method.rsplit(".", 1)[0])
    method = method.rsplit(".", 1)[1]
    try:
        return getattr(module, method)(user)
    except PermissionDenied:
        return False


def get_primary_navigation_items(user):
    """Get the primary navigation items based on user permissions."""
    nav_items = DEFAULT_NAV_ITEMS.copy()
    if settings.APPLY_NAV_MENU_ITEMS:
        nav_items = settings.APPLY_NAV_MENU_ITEMS

    if settings.APPLY_NAV_SUBMISSIONS_ITEMS:
        nav_items[1]["sub_items"] = settings.APPLY_NAV_SUBMISSIONS_ITEMS

    if settings.PROJECTS_ENABLED:
        if settings.APPLY_NAV_PROJECTS_ITEMS:
            nav_items[2]["sub_items"] = settings.APPLY_NAV_PROJECTS_ITEMS
    else:
        nav_items.pop(2)

    temp_nav = nav_items.copy()
    item_count = 0
    for item in nav_items:
        item_count += 1
        removed = False
        if not resolve_and_check_permission(user, item["permission_method"]):
            temp_nav.remove(item)
            removed = True
            item_count -= 1
        if not removed and "sub_items" in item.keys():
            for sub_item in item["sub_items"]:
                if not resolve_and_check_permission(
                    user, sub_item["permission_method"]
                ):
                    temp_nav[item_count]["sub_items"].remove(sub_item)
    return temp_nav
