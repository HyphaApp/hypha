import bleach
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from wagtail.admin.edit_handlers import TabbedInterface, ObjectList, FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField

from opentech.apply.funds.workflow import DETERMINATION_OUTCOMES


REJECTED = 0
NEEDS_MORE_INFO = 1
ACCEPTED = 2

DETERMINATION_CHOICES = (
    (REJECTED, _('Dismissed')),
    (NEEDS_MORE_INFO, _('More information requested')),
    (ACCEPTED, _('Approved')),
)

DETERMINATION_TO_OUTCOME = {
    'rejected': REJECTED,
    'accepted': ACCEPTED,
    'more_info': NEEDS_MORE_INFO,
}

TRANSITION_DETERMINATION = {
    name: DETERMINATION_TO_OUTCOME[type]
    for name, type in DETERMINATION_OUTCOMES.items()
}


class DeterminationQuerySet(models.QuerySet):
    def active(self):
        # Designed to be used with a queryset related to submissions
        return self.get(is_draft=True)

    def submitted(self):
        return self.filter(is_draft=False)

    def final(self):
        return self.submitted().filter(outcome__in=[ACCEPTED, REJECTED])


class Determination(models.Model):
    submission = models.ForeignKey(
        'funds.ApplicationSubmission',
        on_delete=models.CASCADE,
        related_name='determinations'
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

    # Meta: used for migration purposes only
    drupal_id = models.IntegerField(null=True, blank=True, editable=False)

    objects = DeterminationQuerySet.as_manager()

    @property
    def stripped_message(self):
        return bleach.clean(self.message, tags=[], strip=True)

    @property
    def clean_outcome(self):
        return self.get_outcome_display()

    def get_absolute_url(self):
        return reverse('apply:submissions:determinations:detail', args=(self.submission.id, self.id))

    @property
    def submitted(self):
        return not self.is_draft

    def __str__(self):
        return f'Determination for {self.submission.title} by {self.author!s}'

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self.data)}>'

    @property
    def detailed_data(self):
        from .views import get_form_for_stage
        return get_form_for_stage(self.submission).get_detailed_response(self.data)


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


@register_setting
class DeterminationFormSettings(BaseSetting):
    class Meta:
        verbose_name = 'determination settings'

    concept_principles_label = models.CharField('label', default='Goals and principles', max_length=255)
    concept_principles_help_text = models.TextField('help text', blank=True)
    concept_technical_label = models.CharField('label', default='Technical merit', max_length=255)
    concept_technical_help_text = models.TextField('help text', blank=True)
    concept_sustainable_label = models.CharField('label', default='Reasonable, realistic and sustainable', max_length=255)
    concept_sustainable_help_text = models.TextField('help text', blank=True)

    proposal_liked_label = models.CharField('label', default='Positive aspects', max_length=255)
    proposal_liked_help_text = models.TextField('help text', blank=True)
    proposal_concerns_label = models.CharField('label', default='Concerns', max_length=255)
    proposal_concerns_help_text = models.TextField('help text', blank=True)
    proposal_red_flags_label = models.CharField('label', default='Items that must be addressed', max_length=255)
    proposal_red_flags_help_text = models.TextField('help text', blank=True)
    proposal_overview_label = models.CharField('label', default='Project overview questions and comments', max_length=255)
    proposal_overview_help_text = models.TextField('help text', blank=True)
    proposal_objectives_label = models.CharField('label', default='Objectives questions and comments', max_length=255)
    proposal_objectives_help_text = models.TextField('help text', blank=True)
    proposal_strategy_label = models.CharField('label', default='Methods and strategy questions and comments', max_length=255)
    proposal_strategy_help_text = models.TextField('help text', blank=True)
    proposal_technical_label = models.CharField('label', default='Technical feasibility questions and comments', max_length=255)
    proposal_technical_help_text = models.TextField('help text', blank=True)
    proposal_alternative_label = models.CharField('label', default='Alternative analysis - "red teaming" questions and comments', max_length=255)
    proposal_alternative_help_text = models.TextField('help text', blank=True)
    proposal_usability_label = models.CharField('label', default='Usability questions and comments', max_length=255)
    proposal_usability_help_text = models.TextField('help text', blank=True)
    proposal_sustainability_label = models.CharField('label', default='Sustainability questions and comments', max_length=255)
    proposal_sustainability_help_text = models.TextField('help text', blank=True)
    proposal_collaboration_label = models.CharField('label', default='Collaboration questions and comments', max_length=255)
    proposal_collaboration_help_text = models.TextField('help text', blank=True)
    proposal_realism_label = models.CharField('label', default='Cost realism questions and comments', max_length=255)
    proposal_realism_help_text = models.TextField('help text', blank=True)
    proposal_qualifications_label = models.CharField('label', default='Qualifications questions and comments', max_length=255)
    proposal_qualifications_help_text = models.TextField('help text', blank=True)
    proposal_evaluation_label = models.CharField('label', default='Evaluation questions and comments', max_length=255)
    proposal_evaluation_help_text = models.TextField('help text', blank=True)

    concept_help_text_tab_panels = [
        MultiFieldPanel([
            FieldPanel('concept_principles_label'),
            FieldPanel('concept_principles_help_text'),
        ], 'concept principles'),
        MultiFieldPanel([
            FieldPanel('concept_technical_label'),
            FieldPanel('concept_technical_help_text'),
        ], 'concept technical'),
        MultiFieldPanel([
            FieldPanel('concept_sustainable_label'),
            FieldPanel('concept_sustainable_help_text'),
        ], 'concept sustainable'),
    ]

    proposal_help_text_tab_panels = [
        MultiFieldPanel([
            FieldPanel('proposal_liked_label'),
            FieldPanel('proposal_liked_help_text'),
        ], 'proposal liked'),
        MultiFieldPanel([
            FieldPanel('proposal_concerns_label'),
            FieldPanel('proposal_concerns_help_text'),
        ], 'proposal concerns'),
        MultiFieldPanel([
            FieldPanel('proposal_red_flags_label'),
            FieldPanel('proposal_red_flags_help_text'),
        ], 'proposal red flags'),
        MultiFieldPanel([
            FieldPanel('proposal_overview_label'),
            FieldPanel('proposal_overview_help_text'),
        ], 'proposal overview'),
        MultiFieldPanel([
            FieldPanel('proposal_objectives_label'),
            FieldPanel('proposal_objectives_help_text'),
        ], 'proposal objectives'),
        MultiFieldPanel([
            FieldPanel('proposal_strategy_label'),
            FieldPanel('proposal_strategy_help_text'),
        ], 'proposal strategy'),
        MultiFieldPanel([
            FieldPanel('proposal_technical_label'),
            FieldPanel('proposal_technical_help_text'),
        ], 'proposal technical'),
        MultiFieldPanel([
            FieldPanel('proposal_alternative_label'),
            FieldPanel('proposal_alternative_help_text'),
        ], 'proposal alternative'),
        MultiFieldPanel([
            FieldPanel('proposal_usability_label'),
            FieldPanel('proposal_usability_help_text'),
        ], 'proposal usability'),
        MultiFieldPanel([
            FieldPanel('proposal_sustainability_label'),
            FieldPanel('proposal_sustainability_help_text'),
        ], 'proposal sustainability'),
        MultiFieldPanel([
            FieldPanel('proposal_collaboration_label'),
            FieldPanel('proposal_collaboration_help_text'),
        ], 'proposal collaboration'),
        MultiFieldPanel([
            FieldPanel('proposal_realism_label'),
            FieldPanel('proposal_realism_help_text'),
        ], 'proposal realism'),
        MultiFieldPanel([
            FieldPanel('proposal_qualifications_label'),
            FieldPanel('proposal_qualifications_help_text'),
        ], 'proposal qualifications'),
        MultiFieldPanel([
            FieldPanel('proposal_evaluation_label'),
            FieldPanel('proposal_evaluation_help_text'),
        ], 'proposal evaluation'),
    ]

    edit_handler = TabbedInterface([
        ObjectList(concept_help_text_tab_panels, heading='Concept form'),
        ObjectList(proposal_help_text_tab_panels, heading='Proposal form'),
    ])
