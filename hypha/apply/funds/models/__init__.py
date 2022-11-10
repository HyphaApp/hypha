from django.utils.translation import gettext_lazy as _

from .applications import (  # NOQA
    ApplicationBase,
    ApplicationSettings,
    LabBase,
    RoundBase,
    RoundsAndLabs,
)
from .forms import ApplicationForm
from .reminders import Reminder
from .reviewer_role import ReviewerRole, ReviewerSettings
from .screening import ScreeningStatus
from .submissions import ApplicationRevision, ApplicationSubmission, AssignedReviewers

__all__ = [
    'ApplicationSubmission',
    'ApplicationSettings',
    'AssignedReviewers',
    'ApplicationRevision',
    'ApplicationForm',
    'ScreeningStatus',
    'ReviewerRole',
    'Reminder',
    'ReviewerSettings',
]


class FundType(ApplicationBase):
    subpage_types = ['funds.Round']

    class Meta:
        verbose_name = _("Fund")


class RequestForPartners(ApplicationBase):
    subpage_types = ['funds.Round', 'funds.SealedRound']

    class Meta:
        verbose_name = _("RFP")


class Round(RoundBase):
    parent_page_types = ['funds.FundType', 'funds.RequestForPartners']


class SealedRound(RoundBase):
    parent_page_types = ['funds.RequestForPartners']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sealed = True


class LabType(LabBase):
    class Meta:
        verbose_name = _("Lab")
