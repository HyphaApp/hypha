from django.utils.translation import gettext_lazy as _

from hypha.apply.funds.workflows import DETERMINATION_OUTCOMES

REJECTED = 0
NEEDS_MORE_INFO = 1
ACCEPTED = 2

DETERMINATION_CHOICES = (
    (REJECTED, _("Dismissed")),
    (NEEDS_MORE_INFO, _("More information requested")),
    (ACCEPTED, _("Approved")),
)

DETERMINATION_TO_OUTCOME = {
    "rejected": REJECTED,
    "accepted": ACCEPTED,
    "more_info": NEEDS_MORE_INFO,
}

TRANSITION_DETERMINATION = {
    name: DETERMINATION_TO_OUTCOME[type]
    for name, type in DETERMINATION_OUTCOMES.items()
}
