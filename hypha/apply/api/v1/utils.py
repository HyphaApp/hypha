from collections import OrderedDict

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q
from tinymce.widgets import TinyMCE
from wagtail.models import Page

from hypha.apply.categories.models import Option
from hypha.apply.funds.models import ApplicationSubmission, Round, ScreeningStatus
from hypha.apply.review.fields import ScoredAnswerField, ScoredAnswerWidget
from hypha.apply.stream_forms.forms import BlockFieldWrapper
from hypha.apply.users.groups import STAFF_GROUP_NAME

User = get_user_model()


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
        mce_attrs = form_field.widget.mce_attrs
        plugins = mce_attrs.get('plugins')
        if not isinstance(plugins, list):
            mce_attrs['plugins'] = [plugins]
        if 'toolbar1' in mce_attrs:
            mce_attrs['toolbar'] = mce_attrs.pop('toolbar1')
        widget['mce_attrs'] = mce_attrs
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


def get_round_leads():
    return User.objects.filter(submission_lead__isnull=False).distinct()

def get_screening_statuses():
    return ScreeningStatus.objects.filter(
        id__in=ApplicationSubmission.objects.all().values('screening_statuses__id').distinct('screening_statuses__id'))


def get_used_rounds():
    return Round.objects.filter(submissions__isnull=False).distinct()


def get_used_funds():
    # Use page to pick up on both Labs and Funds
    return Page.objects.filter(applicationsubmission__isnull=False).distinct()


def get_category_options():
    return Option.objects.filter(
        category__filter_on_dashboard=True
    )
