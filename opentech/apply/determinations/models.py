from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from opentech.apply.activity.models import Activity

UNAPPROVED = 0
UNDETERMINED = 1
APPROVED = 2

DETERMINATION_CHOICES = (
    (UNAPPROVED, 'Unapproved'),
    (UNDETERMINED, 'Undetermined'),
    (APPROVED, 'Approved'),
)


class Determination(models.Model):
    submission = models.OneToOneField(
        'funds.ApplicationSubmission',
        on_delete=models.CASCADE,
        related_name='determination'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
    )
    determination_data = JSONField()
    determination = models.IntegerField(verbose_name="Determination", choices=DETERMINATION_CHOICES, default=0)
    is_draft = models.BooleanField(default=False, verbose_name="Draft")

    class Meta:
        unique_together = ('author', 'submission')

    def __str__(self):
        return f'Determination for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.determination_responses)}>'


@receiver(post_save, sender=Determination)
def log_determination_activity(sender, **kwargs):
    determination = kwargs.get('instance')

    if kwargs.get('created', False):
        Activity.actions.create(
            user=determination.author,
            submission=determination.submission,
            message=f'Created a determination for {determination.submission.title}'
        )

    if not kwargs.get('is_draft', False):
        Activity.actions.create(
            user=determination.author,
            submission=determination.submission,
            message=f'Sent the determination for {determination.submission.title}'
        )
