import json

from django import forms
from django.forms import widgets
from django.utils.safestring import mark_safe

from django.utils.translation import ugettext_lazy as _
from tinymce import TinyMCE
from wagtail.core.blocks import RichTextBlock

from opentech.apply.review.options import RATE_CHOICES, RECOMMENDATION_CHOICES
from opentech.apply.stream_forms.blocks import OptionalFormFieldBlock, CharFieldBlock, TextFieldBlock
from opentech.apply.utils.blocks import CustomFormFieldsBlock, MustIncludeFieldBlock
from opentech.apply.utils.options import MCE_ATTRIBUTES_SHORT, RICH_TEXT_WIDGET_SHORT


class ScoredAnswerWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        _widgets = (
            TinyMCE(attrs=attrs, mce_attrs=MCE_ATTRIBUTES_SHORT),
            widgets.Select(attrs=attrs, choices=RATE_CHOICES),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            return json.loads(value)
        return [None, None]

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the widget as an HTML string.
        Required for the correct rendering of the TinyMCE widget.
        """
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized
        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)

        rendered = []
        final_attrs = self.build_attrs(attrs)
        input_type = final_attrs.pop('type', None)
        id_ = final_attrs.get('id')
        for i, widget in enumerate(self.widgets):
            if input_type is not None:
                widget.input_type = input_type
            widget_name = '%s_%s' % (name, i)
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                widget_attrs = final_attrs.copy()
                widget_attrs['id'] = '%s_%s' % (id_, i)
            else:
                widget_attrs = final_attrs

            rendered.append(widget.render(widget_name, widget_value, widget_attrs, renderer))

        return ''.join([mark_safe(item) for item in rendered])


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
    widget = RICH_TEXT_WIDGET_SHORT

    class Meta:
        icon = 'openquote'


class ReviewCustomFormFieldsBlock(CustomFormFieldsBlock):
    char = CharFieldBlock(group=_('Fields'))
    text = TextFieldBlock(group=_('Fields'))
    text_markup = RichTextBlock(group=_('Fields'), label=_('Paragraph'))
    score = ScoreFieldBlock(group=_('Fields'))

    required_blocks = ReviewMustIncludeFieldBlock.__subclasses__()
