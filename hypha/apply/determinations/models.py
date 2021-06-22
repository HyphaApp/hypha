import bleach
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from wagtail.admin.edit_handlers import (
    FieldPanel,
    MultiFieldPanel,
    ObjectList,
    StreamFieldPanel,
    TabbedInterface,
)
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.core.fields import RichTextField, StreamField

from hypha.apply.funds.models.mixins import AccessFormData

from .blocks import (
    DeterminationBlock,
    DeterminationCustomFormFieldsBlock,
    DeterminationMessageBlock,
    DeterminationMustIncludeFieldBlock,
    SendNoticeBlock,
)
from .options import ACCEPTED, DETERMINATION_CHOICES, REJECTED


class DeterminationQuerySet(models.QuerySet):
    def active(self):
        # Designed to be used with a queryset related to submissions
        return self.get(is_draft=True)

    def submitted(self):
        return self.filter(is_draft=False)

    def final(self):
        return self.submitted().filter(outcome__in=[ACCEPTED, REJECTED])


class DeterminationFormFieldsMixin(models.Model):
    class Meta:
        abstract = True

    form_fields = StreamField(DeterminationCustomFormFieldsBlock(), default=[])

    @property
    def determination_field(self):
        return self._get_field_type(DeterminationBlock)

    @property
    def message_field(self):
        return self._get_field_type(DeterminationMessageBlock)

    @property
    def send_notice_field(self):
        return self._get_field_type(SendNoticeBlock)

    def _get_field_type(self, block_type, many=False):
        fields = list()
        for field in self.form_fields:
            try:
                if isinstance(field.block, block_type):
                    if many:
                        fields.append(field)
                    else:
                        return field
            except AttributeError:
                pass
        if many:
            return fields


class DeterminationForm(DeterminationFormFieldsMixin, models.Model):
    name = models.CharField(max_length=255)

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('form_fields'),
    ]

    def __str__(self):
        return self.name


class Determination(DeterminationFormFieldsMixin, AccessFormData, models.Model):
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

    # Stores old determination forms data
    data = JSONField(blank=True, null=True)

    # Stores data submitted via streamfield determination forms
    form_data = JSONField(default=dict, encoder=DjangoJSONEncoder)
    is_draft = models.BooleanField(default=False, verbose_name=_("Draft"))
    created_at = models.DateTimeField(verbose_name=_('Creation time'), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_('Update time'), auto_now=True)
    send_notice = models.BooleanField(default=True, verbose_name=_("Send message to applicant"))

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
        return f'<{self.__class__.__name__}: {str(self.form_data)}>'

    @property
    def use_new_determination_form(self):
        """
        Checks if a submission has the new streamfield determination form
        attached to it and along with that it also verify that if self.data is None.

        self.data would be set as None for the determination which are created using
        streamfield determination forms.

        But old lab forms can be edited to add new determination forms
        so we need to use old determination forms for already submitted determination.
        """
        return self.submission.is_determination_form_attached and self.data is None

    @property
    def detailed_data(self):
        if not self.use_new_determination_form:
            from .views import get_form_for_stage
            return get_form_for_stage(self.submission).get_detailed_response(self.data)
        return self.get_detailed_response()

    def get_detailed_response(self):
        data = {}
        group = 0
        data.setdefault(group, {'title': None, 'questions': list()})
        for field in self.form_fields:
            if issubclass(
                field.block.__class__, DeterminationMustIncludeFieldBlock
            ) or isinstance(field.block, SendNoticeBlock):
                continue
            try:
                value = self.form_data[field.id]
            except KeyError:
                group = group + 1
                data.setdefault(group, {'title': field.value.source, 'questions': list()})
            else:
                data[group]['questions'].append(
                    (field.value.get('field_label'), value)
                )
        return data


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

        # requests and external requests use the same messages.
        prefix = prefix.replace("ext", "")

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
        ObjectList(request_tab_panels, heading=_('Request')),
        ObjectList(concept_tab_panels, heading=_('Concept note')),
        ObjectList(proposal_tab_panels, heading=_('Proposal')),
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
        ObjectList(concept_help_text_tab_panels, heading=_('Concept form')),
        ObjectList(proposal_help_text_tab_panels, heading=_('Proposal form')),
    ])
