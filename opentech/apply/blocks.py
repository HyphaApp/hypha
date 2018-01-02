from django import forms
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.blocks import BooleanBlock, ChooserBlock, StreamBlock, StructBlock, StaticBlock
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

    def get_field_class(self, struct_value):
        if struct_value['multi']:
            return forms.MultipleChoiceField
        else:
            return forms.ChoiceField

    def get_field_kwargs(self, struct_value):
        kwargs = super().get_field_kwargs(struct_value)
        category  = struct_value['category']
        choices = category.options.values_list('id', 'value')
        kwargs.update({'choices': choices})
        return kwargs

    def get_widget(self, struct_value):
        if struct_value['multi']:
            return forms.CheckboxSelectMultiple
        else:
            return forms.RadioSelect


class CustomFormFieldsBlock(FormFieldsBlock):
    category = CategoryQuestionBlock(group=_('Custom'))

class FormsBlock(StreamBlock):
    form = StructBlock([
            ('form', StaticBlock(admin_text='Please add additional fields to this form or create an additional form below')),
            ('fields', CustomFormFieldsBlock()),
        ])
