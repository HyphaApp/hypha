from django.utils.translation import ugettext_lazy as _

from .applications import ApplicationBase, RoundBase, LabBase, RoundsAndLabs  # NOQA
from .forms import ApplicationForm
from .reviewer_role import ReviewerRole
from .screening import ScreeningStatus
from .submissions import ApplicationSubmission, AssignedReviewers, ApplicationRevision


__all__ = ['ApplicationSubmission', 'AssignedReviewers', 'ApplicationRevision', 'ApplicationForm', 'ScreeningStatus', 'ReviewerRole']


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
