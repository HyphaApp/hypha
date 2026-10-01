from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import Disbursement
from .project import TrimmedDecimalInput


class TrimmedSignedDecimalInput(TrimmedDecimalInput):
    """``TrimmedDecimalInput`` that also accepts a leading minus, so the
    disbursement amount can record repayments. Scoped to disbursements via a
    dedicated template; the shared ``number.html`` stays positive-only.

    """

    template_name = "django/forms/widgets/number_signed.html"


class DisbursementForm(forms.ModelForm):
    """Create/edit a Disbursement.

    Only the user-editable fields are exposed; ``contract``, ``created_by``
    and ``updated_by`` are set by the views so that the model's ``save()``
    audit log (wagtail.create/wagtail.edit) records the acting user. The
    ``amount`` widget mirrors the contract amount fields so values render
    trimmed but preserve full precision.

    """

    class Meta:
        fields = ["amount", "date", "notes"]
        model = Disbursement
        widgets = {"amount": TrimmedSignedDecimalInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default the date to today so a disbursement recorded on the day it
        # is made does not need re-entering; the model field stays default-free.
        self.fields["date"].initial = timezone.localdate()
        self.fields["amount"].help_text = _(
            "Amount sent to the grantee. Use a negative value to record a repayment."
        )
