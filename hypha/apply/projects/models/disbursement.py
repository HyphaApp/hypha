from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.log_actions import LogContext, log


class Disbursement(models.Model):
    """A single transaction (money sent to, or repaid by, the grantee)
    recorded against a specific Contract.

    Disbursements are recorded by staff without an approval workflow. The
    canonical audit trail is written to Wagtail's ``ModelLogEntry`` via
    ``wagtail.log_actions.log`` (see ``save`` below); activity/messenger
    notices are a separate, best-effort concern handled in the views, not a
    source of truth.

    Negative amounts are permitted so that repayments net out correctly when
    summing disbursements for a contract or project.
    """

    contract = models.ForeignKey(
        "Contract",
        on_delete=models.CASCADE,
        related_name="disbursements",
    )
    # Purposefully large decimal field: support many currencies and inflation.
    # No MinValueValidator: negatives are allowed for repayments.
    amount = models.DecimalField(max_digits=38, decimal_places=19)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="disbursements_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="disbursements_updated",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    wagtail_reference_index_ignore = True

    class Meta:
        verbose_name = _("disbursement")
        verbose_name_plural = _("disbursements")
        ordering = ["-date", "-created_at"]

    def save(self, *args, **kwargs):
        """Audit log all creates and edits to Wagtail's ModelLogEntry.

        Mirrors the pattern in
        hypha/apply/funds/models/application_revisions.py: every save emits a
        wagtail.create/wagtail.edit entry, so the canonical audit trail is
        populated regardless of how the save is triggered. Deletion is logged
        by the DeleteView (which has the request user), not here.
        """
        is_adding = self._state.adding
        super().save(*args, **kwargs)
        with LogContext(user=self.updated_by or self.created_by):
            log(self, "wagtail.create" if is_adding else "wagtail.edit")

    def __str__(self):
        return _("Disbursement of {amount} on {date} for {contract}").format(
            amount=self.amount, date=self.date, contract=self.contract
        )
