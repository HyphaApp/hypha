from django.db import models

from hypha.apply.users.models import User

READ_ONLY = "read_only"
COMMENT = "comment"

COAPPLICANT_ROLE_PERM = {
    READ_ONLY: "can_view",
    COMMENT: "can_comment",
}


class CoApplicantInviteStatus(models.TextChoices):
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
    token = models.CharField(max_length=256, unique=True)
    is_used = models.BooleanField(default=False)
    invited_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="co_applicant_invites",
    )
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
    status = models.CharField(
        max_length=20,
        choices=CoApplicantInviteStatus.choices,
        default=CoApplicantInviteStatus.ACCEPTED,
    )
    accepted_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("submission", "user")

    def __str__(self):
        return self.user
