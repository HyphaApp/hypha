from django.db import models
from django.utils.translation import gettext_lazy as _

from hypha.apply.users.models import User

READ_ONLY = "read_only"
COMMENT = "comment"
EDIT = "edit"

COAPPLICANT_ROLE_CHOICES = (
    (READ_ONLY, _("Read Only")),
    (COMMENT, _("Comment")),
    (EDIT, _("Edit")),
)


class CoApplicantInviteStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class CoApplicantInvite(models.Model):
    submission = models.ForeignKey(
        "funds.ApplicationSubmission",
        on_delete=models.CASCADE,
        related_name="co_applicant_invites",
    )
    invited_user_email = models.EmailField()
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="co_applicant_invites",
    )
    status = models.CharField(
        max_length=20,
        choices=CoApplicantInviteStatus.choices,
        default=CoApplicantInviteStatus.PENDING,
    )
    role = models.CharField(choices=COAPPLICANT_ROLE_CHOICES, default=READ_ONLY)
    responded_on = models.DateTimeField(blank=True, null=True)
    invited_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("submission", "invited_user_email")

    def __str__(self):
        return f"{self.invited_user_email} invited to {self.submission})"


class CoApplicant(models.Model):
    submission = models.ForeignKey(
        "funds.ApplicationSubmission",
        on_delete=models.CASCADE,
        related_name="co_applicants",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="co_applicants"
    )
    invite = models.OneToOneField(
        CoApplicantInvite, on_delete=models.CASCADE, related_name="co_applicant"
    )
    role = models.CharField(choices=COAPPLICANT_ROLE_CHOICES, default=READ_ONLY)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ("submission", "user")

    def __str__(self):
        return self.user.get_display_name()
