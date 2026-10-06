from django import forms
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
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
    trimmed but preserve full precision. The views also pass the related
    ``contract``, whose currency is shown on the ``amount`` label (e.g.
    ``Amount (USD)``) so the unit of the entered amount is unambiguous. On
    create the ``amount`` prepopulates with the contract's approved amount
    (else the project's awarded value) less this contract's existing
    disbursements, still editable.

    """

    class Meta:
        fields = ["amount", "date", "notes"]
        model = Disbursement
        widgets = {"amount": TrimmedSignedDecimalInput()}

    def __init__(self, *args, **kwargs):
        contract = kwargs.pop("contract", None)
        super().__init__(*args, **kwargs)
        # Default the date to today so a disbursement recorded on the day it
        # is made does not need re-entering; the model field stays default-free.
        self.fields["date"].initial = timezone.localdate()
        # Prepopulate with the awarded amount net of this contract's
        # disbursements; editing keeps the instance's recorded amount.
        if self.instance.pk is None:
            awarded = contract.amount_approved if contract is not None else None
            if awarded is None and contract is not None:
                awarded = contract.project.value
            if awarded is not None:
                disbursed = contract.disbursements.aggregate(
                    total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField())
                )["total"]
                self.fields["amount"].initial = awarded - disbursed
        self.fields["amount"].help_text = _(
            "Amount sent to the grantee. Use a negative value to record a repayment."
        )
        # Contract.currency is nullable (old data, other payments flows), so
        # only annotate the label when a code is actually recorded.
        if contract is not None and contract.currency:
            amount_field = self.fields["amount"]
            amount_field.label = f"{amount_field.label} ({contract.currency})"
