from django.db import models

from hypha.apply.users.models import User

READ_ONLY = "read_only"
COMMENT = "comment"

COAPPLICANT_ROLE_PERM = {
    READ_ONLY: "can_view",
    COMMENT: "can_comment",
}


class CoApplicantInviteStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class CoApplicant(models.Model):
    submission = models.ForeignKey(
        "funds.ApplicationSubmission",
        on_delete=models.CASCADE,
        related_name="co_applicants",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="co_applicants"
    )
    role = models.JSONField(default=list)

    status = models.CharField(
        max_length=20,
        choices=CoApplicantInviteStatus.choices,
        default=CoApplicantInviteStatus.PENDING,
    )
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="co_applicant_invites",
    )
    invited_on = models.DateTimeField(auto_now_add=True)
    responded_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("submission", "user")

    def __str__(self):
        return (
            f"{self.user} invited to {self.submission} as {self.role} ({self.status})"
        )
