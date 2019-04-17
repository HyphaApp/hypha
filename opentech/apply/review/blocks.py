import json

from django import forms

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from wagtail.core.blocks import RichTextBlock

from opentech.apply.review.fields import ScoredAnswerField
from opentech.apply.review.options import RECOMMENDATION_CHOICES, RATE_CHOICES_DICT, RATE_CHOICE_NA, NA, VISIBILITY, VISIBILILTY_HELP_TEXT, PRIVATE
from opentech.apply.stream_forms.blocks import OptionalFormFieldBlock, CharFieldBlock, TextFieldBlock, CheckboxFieldBlock, DropdownFieldBlock
from opentech.apply.utils.blocks import CustomFormFieldsBlock, MustIncludeFieldBlock
from opentech.apply.utils.options import RICH_TEXT_WIDGET_SHORT


class ScoreFieldBlock(OptionalFormFieldBlock):
    field_class = ScoredAnswerField

    class Meta:
        label = _('Score')
        icon = 'order'
        template = 'review/render_scored_answer_field.html'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['initial'] = ['', NA]
        return kwargs

    def render(self, value, context=None):
        try:
            comment, score = context['data']
        except ValueError:
            # TODO: Remove json load as data moved away from JSON
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

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['required'] = False
        return kwargs


class VisibilityBlock(ReviewMustIncludeFieldBlock):
    name = 'visibility'
    description = 'Visibility'
    field_class = forms.ChoiceField
    widget = forms.RadioSelect()

    class Meta:
        icon = 'radio-empty'

    def get_field_kwargs(self, struct_value):
        kwargs = super(VisibilityBlock, self).get_field_kwargs(struct_value)
        kwargs['choices'] = VISIBILITY.items()
        kwargs['initial'] = PRIVATE
        kwargs['help_text'] = mark_safe('<br>'.join(
            [VISIBILITY[choice] + ': ' + VISIBILILTY_HELP_TEXT[choice] for choice in VISIBILITY]
        ))
        return kwargs


class ReviewCustomFormFieldsBlock(CustomFormFieldsBlock):
    char = CharFieldBlock(group=_('Fields'))
    text = TextFieldBlock(group=_('Fields'))
    text_markup = RichTextBlock(group=_('Fields'), label=_('Paragraph'))
    score = ScoreFieldBlock(group=_('Fields'))
    checkbox = CheckboxFieldBlock(group=_('Fields'))
    dropdown = DropdownFieldBlock(group=_('Fields'))

    required_blocks = ReviewMustIncludeFieldBlock.__subclasses__()
