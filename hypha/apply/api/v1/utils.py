import inspect
from collections import OrderedDict

from django import forms

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
    return kwargs
