import json

from django import forms

from django.utils.translation import ugettext_lazy as _

from wagtail.core.blocks import RichTextBlock

from opentech.apply.review.fields import ScoredAnswerField
from opentech.apply.review.options import RECOMMENDATION_CHOICES, RATE_CHOICES_DICT, RATE_CHOICE_NA
from opentech.apply.stream_forms.blocks import OptionalFormFieldBlock, CharFieldBlock, TextFieldBlock
from opentech.apply.utils.blocks import CustomFormFieldsBlock, MustIncludeFieldBlock
from opentech.apply.utils.options import RICH_TEXT_WIDGET_SHORT


class ScoreFieldBlock(OptionalFormFieldBlock):
    field_class = ScoredAnswerField

    class Meta:
        label = _('Score')
        icon = 'order'
        template = 'review/render_scored_answer_field.html'

    def render(self, value, context=None):
        comment, score = json.loads(context['data'])
        context.update(**{
            'comment': comment,
            'score': RATE_CHOICES_DICT.get(int(score), RATE_CHOICE_NA)
        })

        return super().render(value, context)


class ReviewMustIncludeFieldBlock(MustIncludeFieldBlock):
    pass


class RecommendationBlock(ReviewMustIncludeFieldBlock):
    name = 'recommendation'
    description = 'Overall recommendation'
    field_class = forms.ChoiceField

    class Meta:
        icon = 'pick'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['choices'] = RECOMMENDATION_CHOICES
        return kwargs

    def render(self, value, context=None):
        data = int(context['data'])
        choices = dict(RECOMMENDATION_CHOICES)
        context['data'] = choices[data]

        return super().render(value, context)


class RecommendationCommentsBlock(ReviewMustIncludeFieldBlock):
    name = 'comments'
    description = 'Recommendation comments'
    widget = RICH_TEXT_WIDGET_SHORT

    class Meta:
        icon = 'openquote'
        template = 'stream_forms/render_unsafe_field.html'


class ReviewCustomFormFieldsBlock(CustomFormFieldsBlock):
    char = CharFieldBlock(group=_('Fields'))
    text = TextFieldBlock(group=_('Fields'))
    text_markup = RichTextBlock(group=_('Fields'), label=_('Paragraph'))
    score = ScoreFieldBlock(group=_('Fields'))

    required_blocks = ReviewMustIncludeFieldBlock.__subclasses__()
