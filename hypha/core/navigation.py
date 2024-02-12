from django.conf import settings
from django.urls import reverse

nav_items = [
    {
        "title": "My Dashboard",
        "url": reverse("dashboard:dashboard"),
        "permission_method": "has_dashboard_access",
    },
    {
        "title": "Submissions",
        "url": reverse(
            "apply:submissions:overview"
        ),  # kind of basic url to figure out active tab
        "permission_method": "is_apply_staff_or_reviewer_required",
        "sub_items": [
            {
                "title": "All Submissions",
                "url": reverse("apply:submissions:list"),
                "permission_method": "is_apply_staff_or_reviewer_required",
            },
            {
                "title": "Staff Assignments",
                "url": reverse("apply:submissions:staff_assignments"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": "Reviews",
                "url": reverse("apply:submissions:reviewer_leaderboard"),
                "permission_method": "is_apply_staff",
            },
            {
                "title": "Results",
                "url": reverse("apply:submissions:result"),
                "permission_method": "is_apply_staff",
            },
        ],
    },
    {
        "title": "Projects",
        "url": reverse(
            "apply:projects:overview"
        ),  # kind of basic url to figure out active tab
        "permission_method": "is_apply_staff_or_finance_or_contracting",
        "sub_items": [
            {
                "title": "All Projects",
                "url": reverse("apply:projects:all"),
                "permission_method": "is_apply_staff_or_finance_or_contracting",
            },
            {
                "title": "Invoices",
                "url": reverse("apply:projects:invoices"),
                "permission_method": "is_apply_staff_or_finance",
            },
            {
                "title": "Reports",
                "url": reverse("apply:projects:reports:all"),
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
