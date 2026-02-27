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
from .co_applicants import CoApplicant, CoApplicantInvite
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
    "CoApplicant",
    "CoApplicantInvite",
]


class FundType(ApplicationBase):
    subpage_types = ["funds.Round"]

    class Meta:
        verbose_name = _("Fund")
        verbose_name_plural = _("Funds")


class RequestForPartners(ApplicationBase):
    subpage_types = ["funds.Round", "funds.SealedRound"]

    class Meta:
        verbose_name = _("RFP")
        verbose_name_plural = _("RFPs")


class Round(RoundBase):
    parent_page_types = ["funds.FundType", "funds.RequestForPartners"]

    class Meta:
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")


class SealedRound(RoundBase):
    parent_page_types = ["funds.RequestForPartners"]

    class Meta:
        verbose_name = _("Sealed round")
        verbose_name_plural = _("Sealed rounds")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sealed = True


class LabType(LabBase):
    class Meta:
        verbose_name = _("Lab")
        verbose_name_plural = _("Labs")
