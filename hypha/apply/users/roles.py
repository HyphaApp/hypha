from django.utils.translation import gettext_lazy as _
from rolepermissions.roles import AbstractUserRole

SUPERADMIN = _("Administrator")
APPLICANT_GROUP_NAME = _("Applicant")
STAFF_GROUP_NAME = _("Staff")
REVIEWER_GROUP_NAME = _("Reviewer")
TEAMADMIN_GROUP_NAME = _("Staff Admin")
PARTNER_GROUP_NAME = _("Partner")
COMMUNITY_REVIEWER_GROUP_NAME = _("Community reviewer")
APPROVER_GROUP_NAME = _("Approver")
FINANCE_GROUP_NAME = _("Finance")
CONTRACTING_GROUP_NAME = _("Contracting")

ROLES_ORG_FACULTY = [
    STAFF_GROUP_NAME,
    TEAMADMIN_GROUP_NAME,
    FINANCE_GROUP_NAME,
    CONTRACTING_GROUP_NAME,
]


# roles for the application
# https://django-role-permissions.readthedocs.io/en/stable/roles.html
class Applicant(AbstractUserRole):
    role_name = APPLICANT_GROUP_NAME
    help_text = _(
        "Can access their own application and communicate via " "the communication tab."
    )

    available_permissions = {}


class Staff(AbstractUserRole):
    role_name = STAFF_GROUP_NAME
    help_text = _(
        "View and edit all submissions, submit reviews, send determinations, "
        "and set up applications."
    )

    available_permissions = {}


class Reviewer(AbstractUserRole):
    role_name = REVIEWER_GROUP_NAME
    help_text = _(
        "Has a dashboard and can submit reviews. "
        "Advisory Council Members are typically assigned this role."
    )

    available_permissions = {}


class StaffAdmin(AbstractUserRole):
    role_name = TEAMADMIN_GROUP_NAME
    help_text = _("Can view application message log. Must also be in group Staff.")

    available_permissions = {}


class Partner(AbstractUserRole):
    role_name = PARTNER_GROUP_NAME
    help_text = _(
        "Can view, edit, and comment on a specific application they are assigned to."
    )

    available_permissions = {}


class CommunityReviewer(AbstractUserRole):
    role_name = COMMUNITY_REVIEWER_GROUP_NAME
    help_text = _(
        "An applicant with access to other applications utilizing the community/peer review workflow."
    )

    available_permissions = {}


class Approver(AbstractUserRole):
    role_name = APPROVER_GROUP_NAME
    help_text = _(
        "Can review/approve project form, and access compliance documents. "
        "Must also be in group: Staff, Contracting, or Finance."
    )

    available_permissions = {}


class Finance(AbstractUserRole):
    role_name = FINANCE_GROUP_NAME
    help_text = _(
        "Can review/approve the project form, access documents associated with "
        "contracting, and access invoices approved by Staff."
    )

    available_permissions = {}


class Contracting(AbstractUserRole):
    role_name = CONTRACTING_GROUP_NAME
    help_text = _(
        "Can review/approve the project form and access documents associated with contracting."
    )

    available_permissions = {}
