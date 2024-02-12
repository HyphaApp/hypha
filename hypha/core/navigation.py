from django.conf import settings
from django.urls import reverse_lazy

nav_items = [
    {
        "title": "My Dashboard",
        "url": reverse_lazy("dashboard:dashboard"),
        "permission_method": "has_dashboard_access",
    },
    {
        "title": "Submissions",
        "url": reverse_lazy(
            "apply:submissions:overview"
        ),  # kind of basic url to figure out active tab
        "permission_method": "is_apply_staff_or_reviewer_required",
        "sub_items": [
            {
                "title": "All Submissions",
                "url": reverse_lazy("apply:submissions:list"),
                "permission_method": "is_apply_staff_or_reviewer_required",
            },
            {
                "title": "Staff Assignments",
                "url": reverse_lazy("apply:submissions:staff_assignments"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": "Reviews",
                "url": reverse_lazy("apply:submissions:reviewer_leaderboard"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": "Results",
                "url": reverse_lazy("apply:submissions:result"),
                "permission_method": "is_apply_staff",
            },
        ],
    },
    {
        "title": "Projects",
        "url": reverse_lazy(
            "apply:projects:overview"
        ),  # kind of basic url to figure out active tab
        "permission_method": "is_apply_staff_or_finance_or_contracting",
        "sub_items": [
            {
                "title": "All Projects",
                "url": reverse_lazy("apply:projects:all"),
                "permission_method": "is_apply_staff_or_finance_or_contracting",
            },
            {
                "title": "Invoices",
                "url": reverse_lazy("apply:projects:invoices"),
                "permission_method": "is_apply_staff_or_finance",
            },
            {
                "title": "Reports",
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
