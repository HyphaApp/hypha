import copy
import functools
import importlib
import logging
import re

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def _check_permission(user, method_path: str) -> bool:
    """Resolve the method path and check if the user has permission.

    Args:
        user: user object
        method_path: import path to the method to check permission

    Returns:
        bool: True if user has permission, False otherwise
    """
    try:
        module_name, method_name = method_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        actual_method = getattr(module, method_name)
        return actual_method(user)
    except PermissionDenied:
        return False
    except (ImportError, AttributeError, ValueError) as e:
        logger.warning(
            f"Permission check failed for method '{method_path}': {e}", exc_info=True
        )
        return False


def _calculate_is_active(
    item_url: str, item_active_regex: str | None, current_path: str
) -> bool:
    """Helper to determine if a nav item is active based on URL or regex."""
    if str(item_url) == current_path:
        return True
    if item_active_regex:
        return bool(re.match(item_active_regex, current_path))
    return False


@functools.cache
def get_primary_navigation_items(request):
    DEFAULT_NAV_ITEMS = [
        {
            "title": _("My Dashboard"),
            "url": reverse_lazy("dashboard:dashboard"),
            "permission_method": "hypha.apply.users.decorators.has_dashboard_access",
        },
        {
            "title": _("Submissions"),
            "url": reverse_lazy("apply:submissions:list"),
            "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_reviewer_required",
            "active_url_regex": r"^(.*)/submissions/(?!.*project)",
            "sub_items": [
                {
                    "title": _("All Submissions"),
                    "url": reverse_lazy("apply:submissions:list"),
                    "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_reviewer_required",
                },
                {
                    "title": _("Rounds & Labs"),
                    "url": reverse_lazy("apply:rounds:list"),
                    "permission_method": "hypha.apply.users.decorators.is_apply_staff",
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
                    "url": reverse_lazy("apply:submissions:list")
                    + "?query=flagged:@staff",
                    "permission_method": "hypha.apply.users.decorators.is_apply_staff",
                },
            ],
        },
        {
            "title": _("Projects"),
            "url": reverse_lazy("apply:projects:all"),
            "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_finance_or_contracting",
            "active_url_regex": r"(.*)/projects?/",
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
                    "url": reverse_lazy("apply:projects:reports:submitted"),
                    "permission_method": "hypha.apply.users.decorators.is_apply_staff_or_finance",
                },
            ],
        },
    ]

    """Get the primary navigation items based on user permissions."""
    original_nav_items = copy.deepcopy(
        settings.APPLY_NAV_MENU_ITEMS or DEFAULT_NAV_ITEMS
    )

    nav_items = []
    request_path = request.path

    for item in original_nav_items:
        nav_item = item.copy()

        if nav_item["title"] == "Projects" and not settings.PROJECTS_ENABLED:
            continue

        if nav_item["title"] == "Submissions" and settings.APPLY_NAV_SUBMISSIONS_ITEMS:
            nav_item["sub_items"] = settings.APPLY_NAV_SUBMISSIONS_ITEMS

        if not _check_permission(request.user, nav_item["permission_method"]):
            continue

        nav_item["is_active"] = _calculate_is_active(
            nav_item["url"], nav_item.get("active_url_regex"), request_path
        )

        if sub_items := nav_item.get("sub_items"):
            filtered_sub_items = []
            any_sub_item_active = False

            for sub_item_original in sub_items:
                sub_item = sub_item_original.copy()  # Ensure we work with a copy
                if _check_permission(request.user, sub_item["permission_method"]):
                    sub_item["is_active"] = _calculate_is_active(
                        sub_item["url"], sub_item.get("active_url_regex"), request_path
                    )
                    if sub_item["is_active"]:
                        any_sub_item_active = True
                    filtered_sub_items.append(sub_item)

            nav_item["sub_items"] = filtered_sub_items

            # If any sub-item is active, mark the main item as active
            # This ensures parent tab is highlighted if a child is active,
            # even if the parent's own URL/regex didn't match.
            if any_sub_item_active:
                nav_item["is_active"] = True

        nav_items.append(nav_item)

    return nav_items
