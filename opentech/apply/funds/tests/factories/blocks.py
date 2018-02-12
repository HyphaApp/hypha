import wagtail_factories

from opentech.apply.stream_forms.blocks import FormFieldBlock
from opentech.apply.funds import blocks


__all__ = ['CustomFormFieldsFactory', 'FormFieldBlock', 'FullNameBlockFactory', 'EmailBlockFactory']


class FormFieldBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = FormFieldBlock


class EmailBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.EmailBlock


class FullNameBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.FullNameBlock


CustomFormFieldsFactory = wagtail_factories.StreamFieldFactory({
    'email': EmailBlockFactory,
    'full_name': FullNameBlockFactory,
})
