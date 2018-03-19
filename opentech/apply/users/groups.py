STAFF_GROUP_NAME = 'Staff'
REVIEWER_GROUP_NAME = 'Reviewer'

GROUPS = [
    {
        'name': 'Applicant',
        'permissions': [],
    },
    {
        'name': REVIEWER_GROUP_NAME,
        'permissions': [],
    },
    {
        'name': 'Advisor',
        'permissions': [],
    },
    {
        'name': STAFF_GROUP_NAME,
        'permissions': [],
    },
    {
        'name': 'Manager',
        'permissions': [
            'add_image',
            'change_image',
            'delete_image',
            'add_document',
            'change_document',
            'delete_document',
            'access_admin',
        ],
    },
    {
        'name': 'Administrator',
        'permissions': [
            'add_image',
            'change_image',
            'delete_image',
            'add_document',
            'change_document',
            'delete_document',
            'add_user',
            'change_user',
            'delete_user',
            'access_admin',
            'change_site',
        ],
    }
]
