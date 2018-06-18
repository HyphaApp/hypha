from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from opentech.apply.activity.models import Activity

UNAPPROVED = 0
UNDETERMINED = 1
APPROVED = 2

DETERMINATION_CHOICES = (
    (UNAPPROVED, _('Rejected')),
    (UNDETERMINED, _('Needs more info')),
    (APPROVED, _('Accepted')),
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

    determination = models.IntegerField(verbose_name=_("Determination"), choices=DETERMINATION_CHOICES, default=0)
    determination_message = models.TextField(verbose_name=_("Determination message"), blank=True)
    determination_data = JSONField()
    is_draft = models.BooleanField(default=False, verbose_name=_("Draft"))
    created_at = models.DateTimeField(verbose_name=_('Creation time'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('Update time'), auto_now=True)

    class Meta:
        unique_together = ('author', 'submission')

    def get_absolute_url(self):
        return reverse('apply:submissions:determinations:detail', args=(self.id,))

    def __str__(self):
        return f'Determination for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.determination_data)}>'


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
