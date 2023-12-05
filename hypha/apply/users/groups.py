from django.utils.translation import gettext_lazy as _

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

APPLICANT_HELP_TEXT = _(
    "Can access their own application and communicate via the communication tab."
)
STAFF_HELP_TEXT = _(
    "View and edit all submissions, submit reviews, send determinations, and set up applications."
)
REVIEWER_HELP_TEXT = _(
    "Has a dashboard and can submit reviews. Advisory Council Members are typically assigned this role."
)

TEAMADMIN_HELP_TEXT = _(
    "Can view application message log. Must also be in group Staff."
)

PARTNER_HELP_TEXT = _(
    "Can view, edit, and comment on a specific application they are assigned to."
)

COMMUNITY_REVIEWER_HELP_TEXT = _(
    "An applicant with access to other applications utilizing the community/peer review workflow."
)

APPROVER_HELP_TEXT = _(
    "Can review/approve PAF, and access compliance documents. Must also be in group: Staff, Contracting, or Finance."
)
FINANCE_HELP_TEXT = _(
    "Can review/approve the PAF, access documents associated with contracting, and access invoices approved by Staff."
)
CONTRACTING_HELP_TEXT = _(
    "Can review/approve the PAF and access documents associated with contracting."
)


GROUPS = [
    {
        "name": APPLICANT_GROUP_NAME,
        "permissions": [],
        "help_text": APPLICANT_HELP_TEXT,
    },
    {
        "name": STAFF_GROUP_NAME,
        "permissions": [],
        "help_text": STAFF_HELP_TEXT,
    },
    {
        "name": REVIEWER_GROUP_NAME,
        "permissions": [],
        "help_text": REVIEWER_HELP_TEXT,
    },
    {
        "name": TEAMADMIN_GROUP_NAME,
        "permissions": [],
        "help_text": TEAMADMIN_HELP_TEXT,
    },
    {
        "name": PARTNER_GROUP_NAME,
        "permissions": [],
        "help_text": PARTNER_HELP_TEXT,
    },
    {
        "name": COMMUNITY_REVIEWER_GROUP_NAME,
        "permissions": [],
        "help_text": COMMUNITY_REVIEWER_HELP_TEXT,
    },
    {
        "name": APPROVER_GROUP_NAME,
        "permissions": [],
        "help_text": APPROVER_HELP_TEXT,
    },
    {
        "name": FINANCE_GROUP_NAME,
        "permissions": [],
        "help_text": FINANCE_HELP_TEXT,
    },
    {
        "name": CONTRACTING_GROUP_NAME,
        "permissions": [],
        "help_text": CONTRACTING_HELP_TEXT,
    },
]
