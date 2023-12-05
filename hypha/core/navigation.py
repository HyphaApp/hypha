from hypha.apply.users.groups import (
    APPLICANT_GROUP_NAME,
    APPROVER_GROUP_NAME,
    COMMUNITY_REVIEWER_GROUP_NAME,
    CONTRACTING_GROUP_NAME,
    FINANCE_GROUP_NAME,
    PARTNER_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
    TEAMADMIN_GROUP_NAME,
)

nav_items = [
    {
        "title": "My Dashboard",
        "url": "dashboard:dashboard",
        "user_roles": [
            STAFF_GROUP_NAME,
            APPROVER_GROUP_NAME,
            APPLICANT_GROUP_NAME,
            REVIEWER_GROUP_NAME,
            CONTRACTING_GROUP_NAME,
            FINANCE_GROUP_NAME,
            PARTNER_GROUP_NAME,
            TEAMADMIN_GROUP_NAME,
            COMMUNITY_REVIEWER_GROUP_NAME,
        ],
    },
    {
        "title": "Submissions",
        "url": "apply:submissions:overview",  # kind of basic url to figure out active tab
        "user_roles": [STAFF_GROUP_NAME, TEAMADMIN_GROUP_NAME],
        "categories": [
            {
                "title": "All Submissions",
                "url": "apply:submissions:list",
                "user_roles": [STAFF_GROUP_NAME, TEAMADMIN_GROUP_NAME],
            },
            {
                "title": "Staff Assignments",
                "url": "apply:submissions:staff_assignments",
                "user_roles": [STAFF_GROUP_NAME, TEAMADMIN_GROUP_NAME],
            },
            {
                "title": "Reviews",
                "url": "apply:submissions:reviewer_leaderboard",
                "user_roles": [STAFF_GROUP_NAME, TEAMADMIN_GROUP_NAME],
            },
            {
                "title": "Results",
                "url": "apply:submissions:result",
                "user_roles": [STAFF_GROUP_NAME, TEAMADMIN_GROUP_NAME],
            },
        ],
    },
    {
        "title": "Projects",
        "url": "apply:projects:overview",  # kind of basic url to figure out active tab
        "user_roles": [
            STAFF_GROUP_NAME,
            TEAMADMIN_GROUP_NAME,
            FINANCE_GROUP_NAME,
            CONTRACTING_GROUP_NAME,
        ],
        "categories": [
            {
                "title": "All Projects",
                "url": "apply:projects:all",
                "user_roles": [
                    STAFF_GROUP_NAME,
                    TEAMADMIN_GROUP_NAME,
                    FINANCE_GROUP_NAME,
                    CONTRACTING_GROUP_NAME,
                ],
            },
            {
                "title": "Invoices",
                "url": "apply:projects:invoices",
                "user_roles": [
                    STAFF_GROUP_NAME,
                    TEAMADMIN_GROUP_NAME,
                    FINANCE_GROUP_NAME,
                ],
            },
            {
                "title": "Reports",
                "url": "apply:projects:reports:all",
                "user_roles": [
                    STAFF_GROUP_NAME,
                    TEAMADMIN_GROUP_NAME,
                    FINANCE_GROUP_NAME,
                ],
            },
        ],
    },
]
