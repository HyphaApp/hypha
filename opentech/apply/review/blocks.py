import json

from django import forms
from django.forms import widgets

from django.utils.translation import ugettext_lazy as _
from wagtail.core.blocks import RichTextBlock

from opentech.apply.review.options import RATE_CHOICES, RECOMMENDATION_CHOICES
from opentech.apply.stream_forms.blocks import OptionalFormFieldBlock, CharFieldBlock, TextFieldBlock
from opentech.apply.utils.blocks import CustomFormFieldsBlock, MustIncludeFieldBlock


class ScoredAnswerWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        text_attrs = attrs if attrs is not None else {}
        text_attrs['rows'] = 5

        _widgets = (
            widgets.Textarea(attrs=text_attrs),
            widgets.Select(attrs=attrs, choices=RATE_CHOICES),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return json.loads(value)
        return [None, None]


class ScoredAnswerField(forms.MultiValueField):
    widget = ScoredAnswerWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(),
            forms.ChoiceField(choices=RATE_CHOICES),
        )

        super().__init__(fields=fields, *args, **kwargs)

    def compress(self, data_list):
        return json.dumps(data_list)


class ScoreFieldBlock(OptionalFormFieldBlock):

    field_class = ScoredAnswerField

    class Meta:
        label = _('Score')
        icon = 'order'


class ReviewMustIncludeFieldBlock(MustIncludeFieldBlock):
    pass


class RecommendationBlock(ReviewMustIncludeFieldBlock):
    name = 'Recommendation'
    description = 'Overall recommendation'
    field_class = forms.ChoiceField

    class Meta:
        icon = 'pick'

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        kwargs['choices'] = RECOMMENDATION_CHOICES
        return kwargs


class RecommendationCommentsBlock(ReviewMustIncludeFieldBlock):
    name = 'Comments'
    description = 'Recommendation comments'

    class Meta:
        icon = 'openquote'


class ReviewCustomFormFieldsBlock(CustomFormFieldsBlock):
    char = CharFieldBlock(group=_('Fields'))
    text = TextFieldBlock(group=_('Fields'))
    text_markup = RichTextBlock(group=_('Fields'), label=_('Paragraph'))
    score = ScoreFieldBlock(group=_('Fields'))

    required_blocks = ReviewMustIncludeFieldBlock.__subclasses__()
