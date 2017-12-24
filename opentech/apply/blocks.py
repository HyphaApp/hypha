from django import forms
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.blocks import BooleanBlock, ChooserBlock
from wagtail.wagtailcore.utils import resolve_model_string

from opentech.stream_forms.blocks import FormFieldBlock, FormFieldsBlock


class CategoryChooserBlock(ChooserBlock):
    widget = forms.Select

    def __init__(self, target_model, **kwargs):
        self._target_model = target_model
        super().__init__(**kwargs)

    @cached_property
    def target_model(self):
        return resolve_model_string(self._target_model)


class CategoryQuestionBlock(FormFieldBlock):
    category = CategoryChooserBlock('apply.Category')
    multi = BooleanBlock(label='Multi select', required=False)

    field_class = forms.MultipleChoiceField

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        options = struct_value['category'].options.all()
        choices = ((option.id, option.value) for option in options)
        kwargs.update({'choices': choices})
        return kwargs

    def get_widget(self, struct_value):
        if struct_value['multi']:
            return forms.CheckboxSelectMultiple
        else:
            return forms.RadioSelect


class CustomFormFieldsBlock(FormFieldsBlock):
    category = CategoryQuestionBlock(group=_('Custom'))
