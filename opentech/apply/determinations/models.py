import bleach
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.edit_handlers import TabbedInterface, ObjectList, FieldPanel
from wagtail.contrib.settings.models import BaseSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.core.fields import RichTextField

from opentech.apply.activity.models import Activity

REJECTED = 0
NEEDS_MORE_INFO = 1
ACCEPTED = 2

DETERMINATION_CHOICES = (
    (REJECTED, _('Rejected')),
    (NEEDS_MORE_INFO, _('Needs more info')),
    (ACCEPTED, _('Accepted')),
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

    outcome = models.IntegerField(verbose_name=_("Determination"), choices=DETERMINATION_CHOICES, default=1)
    message = models.TextField(verbose_name=_("Determination message"), blank=True)
    data = JSONField(blank=True)
    is_draft = models.BooleanField(default=False, verbose_name=_("Draft"))
    created_at = models.DateTimeField(verbose_name=_('Creation time'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('Update time'), auto_now=True)

    class Meta:
        unique_together = ('author', 'submission')

    def get_absolute_url(self):
        return reverse('apply:submissions:determinations:detail', args=(self.id,))

    def submitted(self):
        return self.outcome != NEEDS_MORE_INFO and not self.is_draft

    def __str__(self):
        return f'Determination for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.data)}>'


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
        submission = determination.submission
        message = bleach.clean(determination.message, tags=[], strip=True)
        outcome = determination.get_outcome_display()
        Activity.actions.create(
            user=determination.author,
            submission=submission,
            message=f"Sent a {outcome} determination for {submission.title}:\r\n{message}"
        )


@register_setting
class DeterminationMessageSettings(BaseSetting):
    class Meta:
        verbose_name = 'determination messages'

    concept_accepted = RichTextField("Accepted")
    concept_rejected = RichTextField("Rejected")
    concept_more_info = RichTextField("Needs more info")

    proposal_accepted = RichTextField("Accepted")
    proposal_rejected = RichTextField("Rejected")
    proposal_more_info = RichTextField("Needs more info")

    concept_tab_panels = [
        FieldPanel('concept_accepted'),
        FieldPanel('concept_rejected'),
        FieldPanel('concept_more_info'),
    ]
    proposal_tab_panels = [
        FieldPanel('proposal_accepted'),
        FieldPanel('proposal_rejected'),
        FieldPanel('proposal_more_info'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(concept_tab_panels, heading='Concept note'),
        ObjectList(proposal_tab_panels, heading='Proposal'),
    ])
