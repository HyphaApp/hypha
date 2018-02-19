from wagtail.wagtailcore.blocks import CharBlock
import wagtail_factories

from opentech.apply.stream_forms.blocks import FormFieldBlock, CharFieldBlock, RadioButtonsFieldBlock
from opentech.apply.funds import blocks


__all__ = ['CustomFormFieldsFactory', 'FormFieldBlock', 'FullNameBlockFactory', 'EmailBlockFactory']


class CharBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = CharBlock


class FormFieldBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = FormFieldBlock


class CharFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = CharFieldBlock


class RadioFieldBlockFactory(FormFieldBlockFactory):
    choices = wagtail_factories.ListBlockFactory(CharBlockFactory)

    class Meta:
        model = RadioButtonsFieldBlock


class EmailBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.EmailBlock


class FullNameBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.FullNameBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RichTextFieldBlock


CustomFormFieldsFactory = wagtail_factories.StreamFieldFactory({
    'email': EmailBlockFactory,
    'full_name': FullNameBlockFactory,
    'char': CharFieldBlockFactory,
    'radios': RadioFieldBlockFactory,
    'rich_text': RichTextFieldBlockFactory,
})
