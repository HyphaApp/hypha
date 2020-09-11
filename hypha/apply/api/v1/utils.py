import inspect
from collections import OrderedDict

from django import forms
from tinymce.widgets import TinyMCE

from hypha.apply.review.fields import ScoredAnswerField, ScoredAnswerWidget
from hypha.apply.stream_forms.forms import BlockFieldWrapper

IGNORE_ARGS = ['self', 'cls']


def find_function_args(func):
    """
    Get the list of parameter names which function accepts.
    """
    try:
        spec = inspect.getfullargspec(func) if hasattr(inspect, 'getfullargspec') else inspect.getargspec(func)
        return [i for i in spec[0] if i not in IGNORE_ARGS]
    except TypeError:
        return []


def find_class_args(klass):
    """
    Find all class arguments (parameters) which can be passed in ``__init__``.
    """
    args = set()

    for i in klass.mro():
        if i is object or not hasattr(i, '__init__'):
            continue
        args |= set(find_function_args(i.__init__))

    return list(args)


def get_field_kwargs(form_field):
    if isinstance(form_field, BlockFieldWrapper):
        return {'text': form_field.block.value.source}
    kwargs = OrderedDict()
    kwargs = {
        'initial': form_field.initial,
        'required': form_field.required,
        'label': form_field.label,
        'label_suffix': form_field.label_suffix,
        'help_text': form_field.help_text,
        'help_link': form_field.help_link
    }
    if isinstance(form_field, forms.CharField):
        if hasattr(form_field, 'word_limit'):
            kwargs['word_limit'] = form_field.word_limit
        kwargs['max_length'] = form_field.max_length
        kwargs['min_length'] = form_field.min_length
        kwargs['empty_value'] = form_field.empty_value
    if isinstance(form_field, forms.ChoiceField):
        kwargs['choices'] = form_field.choices
    if isinstance(form_field, forms.TypedChoiceField):
        kwargs['coerce'] = form_field.coerce
        kwargs['empty_value'] = form_field.empty_value
    if isinstance(form_field, forms.IntegerField):
        kwargs['max_value'] = form_field.max_value
        kwargs['min_value'] = form_field.min_value
    if isinstance(form_field, ScoredAnswerField):
        fields = [
            {
                'type': form_field.fields[0].__class__.__name__,
                'max_length': form_field.fields[0].max_length,
                'min_length': form_field.fields[0].min_length,
                'empty_value': form_field.fields[0].empty_value
            },
            {
                'type': form_field.fields[1].__class__.__name__,
                'choices': form_field.fields[1].choices,
            },
        ]
        kwargs['fields'] = fields
    return kwargs


def get_field_widget(form_field):
    if isinstance(form_field, BlockFieldWrapper):
        return {'type': 'LoadHTML', 'attrs': {}}
    widget = {
        'type': form_field.widget.__class__.__name__,
        'attrs': form_field.widget.attrs
    }
    if isinstance(form_field.widget, TinyMCE):
        widget['mce_attrs'] = form_field.widget.mce_attrs
    if isinstance(form_field.widget, ScoredAnswerWidget):
        field_widgets = form_field.widget.widgets
        widgets = [
            {
                'type': field_widgets[0].__class__.__name__,
                'attrs': field_widgets[0].attrs,
                'mce_attrs': field_widgets[0].mce_attrs
            },
            {
                'type': field_widgets[1].__class__.__name__,
                'attrs': field_widgets[1].attrs,
            }
        ]
        widget['widgets'] = widgets
    return widget
