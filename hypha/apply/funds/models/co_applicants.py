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
    responded_on = models.DateTimeField(blank=True, null=True)
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
    role = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ("submission", "user")

    def __str__(self):
        return self.user
