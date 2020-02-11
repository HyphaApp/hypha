from django import forms

from .options import RICH_TEXT_WIDGET


class RichTextField(forms.CharField):
    widget = RICH_TEXT_WIDGET

    def __init__(self, *args, required=False, **kwargs):
        kwargs.update(required=required)
        super().__init__(*args, **kwargs)
