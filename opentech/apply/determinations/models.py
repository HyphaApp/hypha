import bleach
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.edit_handlers import TabbedInterface, ObjectList, FieldPanel
from wagtail.contrib.settings.models import BaseSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.core.fields import RichTextField


REJECTED = 0
NEEDS_MORE_INFO = 1
ACCEPTED = 2

DETERMINATION_CHOICES = (
    (REJECTED, _('Dismissed')),
    (NEEDS_MORE_INFO, _('Needs more info')),
    (ACCEPTED, _('Approved')),
)

DETERMINATION_TRANSITION_SUFFIX = {
    ACCEPTED: ['accepted', 'invited_to_proposal'],
    REJECTED: ['rejected'],
    NEEDS_MORE_INFO: ['more_info'],
}


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

    @property
    def clean_message(self):
        return bleach.clean(self.message, tags=[], strip=True)

    def get_absolute_url(self):
        return reverse('apply:submissions:determinations:detail', args=(self.id,))

    @property
    def submitted(self):
        return self.outcome != NEEDS_MORE_INFO and not self.is_draft

    def __str__(self):
        return f'Determination for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.data)}>'


@register_setting
class DeterminationMessageSettings(BaseSetting):
    class Meta:
        verbose_name = 'determination messages'

    request_accepted = RichTextField("Approved")
    request_rejected = RichTextField("Dismissed")
    request_more_info = RichTextField("Needs more info")

    concept_accepted = RichTextField("Approved")
    concept_rejected = RichTextField("Dismissed")
    concept_more_info = RichTextField("Needs more info")

    proposal_accepted = RichTextField("Approved")
    proposal_rejected = RichTextField("Dismissed")
    proposal_more_info = RichTextField("Needs more info")

    def get_for_stage(self, stage_name):
        message_templates = {}
        prefix = f"{stage_name.lower()}_"

        for field in self._meta.get_fields():
            if prefix in field.name:
                key = field.name.replace(prefix, '')
                message_templates[key] = getattr(self, field.name)

        return message_templates

    request_tab_panels = [
        FieldPanel('request_accepted'),
        FieldPanel('request_rejected'),
        FieldPanel('request_more_info'),
    ]

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
        ObjectList(request_tab_panels, heading='Request'),
        ObjectList(concept_tab_panels, heading='Concept note'),
        ObjectList(proposal_tab_panels, heading='Proposal'),
    ])
