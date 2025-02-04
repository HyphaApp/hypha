from django.contrib.admin import display
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

    @property
    def application_forms(self):
        # Return related forms as a comma-separated list
        return ", ".join(form.form.name for form in self.forms.all())

    @property
    @display(description=_("Review Forms"))
    def get_review_forms(self):
        # Return related forms as a comma-separated list
        return ", ".join(form.form.name for form in self.review_forms.all())

    @property
    @display(description=_("Determination Forms"))
    def get_determination_forms(self):
        # Return related forms as a comma-separated list
        return ", ".join(form.form.name for form in self.determination_forms.all())


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

    @property
    def application_forms(self):
        # Return related forms as a comma-separated list
        return ", ".join(form.form.name for form in self.forms.all())

    @property
    @display(description=_("Review Forms"))
    def get_review_forms(self):
        # Return related forms as a comma-separated list
        return ", ".join(form.form.name for form in self.review_forms.all())

    @property
    @display(description=_("Determination Forms"))
    def get_determination_forms(self):
        # Return related forms as a comma-separated list
        return ", ".join(form.form.name for form in self.determination_forms.all())
