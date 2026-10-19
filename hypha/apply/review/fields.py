from django import forms
from django.db.models import BLANK_CHOICE_DASH
from django.forms import widgets
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE

from hypha.apply.review.options import NA, RATE_CHOICES
from hypha.apply.utils.options import MCE_ATTRIBUTES_SHORT


def get_score_choices():
    """
    The NA choice is the default. If it is disabled, add an empty choice
    in its place so no score is preselected.
    """
    if NA in dict(RATE_CHOICES):
        return RATE_CHOICES
    return tuple(BLANK_CHOICE_DASH) + RATE_CHOICES


class ScoredAnswerWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        _widgets = (
            TinyMCE(attrs=attrs, mce_attrs=MCE_ATTRIBUTES_SHORT),
            widgets.Select(
                attrs={"data-score-field": "true"}, choices=get_score_choices()
            ),
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
        for kwargs, widget in zip(
            context["widget"]["subwidgets"], self.widgets, strict=False
        ):
            name = kwargs["name"]
            value = kwargs["value"]
            attrs = kwargs["attrs"]
            rendered.append(widget.render(name, value, attrs, renderer))
        return mark_safe("".join(list(rendered)))


class ScoredAnswerField(forms.MultiValueField):
    widget = ScoredAnswerWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.CharField(),
            forms.ChoiceField(choices=get_score_choices()),
        )

        super().__init__(*args, **kwargs, fields=fields)

    def compress(self, data_list):
        if data_list:
            # An empty score is only possible when NA is disabled.
            score = data_list[1]
            return [data_list[0], int(score) if score != "" else NA]
        else:
            return ["", NA]
