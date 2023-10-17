from django.utils.translation import gettext_lazy as _

from .application_revisions import ApplicationRevision
from .applications import (
    ApplicationBase,
    ApplicationSettings,
    LabBase,
    RoundBase,
    RoundsAndLabs,
)
from .assigned_reviewers import AssignedReviewers
from .forms import ApplicationForm
from .reminders import Reminder
from .reviewer_role import ReviewerRole, ReviewerSettings
from .screening import ScreeningStatus
from .submissions import ApplicationSubmission

__all__ = [
    "ApplicationForm",
    "ApplicationRevision",
    "ApplicationSettings",
    "ApplicationSubmission",
    "AssignedReviewers",
    "Reminder",
    "ReviewerRole",
    "ReviewerSettings",
    "RoundsAndLabs",
    "ScreeningStatus",
]


class FundType(ApplicationBase):
    subpage_types = ["funds.Round"]

    class Meta:
        verbose_name = _("Fund")


class RequestForPartners(ApplicationBase):
    subpage_types = ["funds.Round", "funds.SealedRound"]

    class Meta:
        verbose_name = _("RFP")


class Round(RoundBase):
    parent_page_types = ["funds.FundType", "funds.RequestForPartners"]


class SealedRound(RoundBase):
    parent_page_types = ["funds.RequestForPartners"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sealed = True


class LabType(LabBase):
    class Meta:
        verbose_name = _("Lab")
