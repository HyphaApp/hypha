from django import forms
from tinymce import TinyMCE

from django.forms import widgets
from django.utils.safestring import mark_safe

from opentech.apply.review.options import RATE_CHOICES
from opentech.apply.utils.options import MCE_ATTRIBUTES_SHORT


class ScoredAnswerWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        _widgets = (
            TinyMCE(attrs=attrs, mce_attrs=MCE_ATTRIBUTES_SHORT),
            widgets.Select(attrs=attrs, choices=RATE_CHOICES),
        )
        super().__init__(_widgets, attrs)

    def decompress(self, value):
        # We should only hit this on initialisation where we set the default to a list of None
        if value:
            return value
        return [None, None]

    def render(self, name, value, attrs=None, renderer=None):
        context = self.get_context(name, value, attrs)
        rendered = []
        # We need to explicitly call the render method on the tinymce widget
        # MultiValueWidget just passes all the context into the template
        for kwargs, widget in zip(context['widget']['subwidgets'], self.widgets):
            name = kwargs['name']
            value = kwargs['value']
            attrs = kwargs['attrs']
            rendered.append(widget.render(name, value, attrs, renderer))
        return mark_safe(''.join([widget for widget in rendered]))


class ScoredAnswerField(forms.MultiValueField):
    widget = ScoredAnswerWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(),
            forms.ChoiceField(choices=RATE_CHOICES),
        )

        super().__init__(fields=fields, *args, **kwargs)

    def compress(self, data_list):
        return [data_list[0], int(data_list[1])]
