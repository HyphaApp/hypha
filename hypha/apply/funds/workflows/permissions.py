from enum import Enum


class UserPermissions(Enum):
    STAFF = 1
    ADMIN = 2
    LEAD = 3
    APPLICANT = 4


class Permissions:
    def __init__(self, permissions):
        self.permissions = permissions

    def can_do(self, user, action):
        checks = self.permissions.get(action, [])
        return any(check(user) for check in checks)

    def can_edit(self, user):
        return self.can_do(user, 'edit')

    def can_review(self, user):
        return self.can_do(user, 'review')

    def can_view(self, user):
        return self.can_do(user, 'view')


staff_can = lambda user: user.is_apply_staff  # NOQA

applicant_can = lambda user: user.is_applicant  # NOQA

reviewer_can = lambda user: user.is_reviewer  # NOQA

partner_can = lambda user: user.is_partner  # NOQA

community_can = lambda user: user.is_community_reviewer  # NOQA


def make_permissions(edit=None, review=None, view=None):
    return {
        'edit': edit or [],
        'review': review or [],
        'view': view or [staff_can, applicant_can, reviewer_can, partner_can],
    }


no_permissions = make_permissions()

default_permissions = make_permissions(edit=[staff_can], review=[staff_can])

hidden_from_applicant_permissions = make_permissions(
    edit=[staff_can], review=[staff_can], view=[staff_can, reviewer_can]
)

reviewer_review_permissions = make_permissions(
    edit=[staff_can], review=[staff_can, reviewer_can]
)

community_review_permissions = make_permissions(
    edit=[staff_can], review=[staff_can, reviewer_can, community_can]
)

applicant_edit_permissions = make_permissions(
    edit=[applicant_can, partner_can], review=[staff_can]
)

staff_edit_permissions = make_permissions(edit=[staff_can])
