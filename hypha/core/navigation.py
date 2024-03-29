from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

nav_items = [
    {
        "title": _("My Dashboard"),
        "url": reverse_lazy("dashboard:dashboard"),
        "permission_method": "has_dashboard_access",
    },
    {
        "title": _("Submissions"),
        # kind of basic url to figure out active tab
        "url": reverse_lazy("apply:submissions:overview"),
        "permission_method": "is_apply_staff_or_reviewer_required",
        "sub_items": [
            {
                "title": _("All Submissions"),
                "url": reverse_lazy("apply:submissions:list"),
                "permission_method": "is_apply_staff_or_reviewer_required",
            },
            {
                "title": _("Staff Assignments"),
                "url": reverse_lazy("apply:submissions:staff_assignments"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": _("Reviews"),
                "url": reverse_lazy("apply:submissions:reviewer_leaderboard"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": _("Results"),
                "url": reverse_lazy("apply:submissions:result"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": _("Staff flagged"),
                "url": reverse_lazy("apply:submissions:staff_flagged"),
                "permission_method": "is_apply_staff",
            },
        ],
    },
    {
        "title": _("Projects"),
        # kind of basic url to figure out active tab
        "url": reverse_lazy("apply:projects:overview"),
        "permission_method": "is_apply_staff_or_finance_or_contracting",
        "sub_items": [
            {
                "title": _("All Projects"),
                "url": reverse_lazy("apply:projects:all"),
                "permission_method": "is_apply_staff_or_finance_or_contracting",
            },
            {
                "title": _("Invoices"),
                "url": reverse_lazy("apply:projects:invoices"),
                "permission_method": "is_apply_staff_or_finance",
            },
            {
                "title": _("Reports"),
                "url": reverse_lazy("apply:projects:reports:all"),
                "permission_method": "is_apply_staff_or_finance",
            },
        ],
    },
]


if settings.APPLY_NAV_MENU_ITEMS:
    nav_items = settings.APPLY_NAV_MENU_ITEMS

if settings.APPLY_NAV_SUBMISSIONS_ITEMS:
    nav_items[1]["sub_items"] = settings.APPLY_NAV_SUBMISSIONS_ITEMS

if settings.APPLY_NAV_PROJECTS_ITEMS:
    nav_items[2]["sub_items"] = settings.APPLY_NAV_PROJECTS_ITEMS
