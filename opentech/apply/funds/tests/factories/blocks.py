import json
import uuid

from wagtail.wagtailcore.blocks import CharBlock
import wagtail_factories

from opentech.apply.stream_forms import blocks as stream_blocks
from opentech.apply.funds import blocks


__all__ = ['CustomFormFieldsFactory', 'FormFieldBlockFactory', 'FullNameBlockFactory', 'EmailBlockFactory']


class CharBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = CharBlock


class FormFieldBlockFactory(wagtail_factories.StructBlockFactory):
    class Meta:
        model = stream_blocks.FormFieldBlock


class CharFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = stream_blocks.CharFieldBlock


class NumberFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = stream_blocks.NumberFieldBlock


class RadioFieldBlockFactory(FormFieldBlockFactory):
    choices = wagtail_factories.ListBlockFactory(CharBlockFactory)

    class Meta:
        model = stream_blocks.RadioButtonsFieldBlock


class TitleBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.TitleBlock


class EmailBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.EmailBlock


class FullNameBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.FullNameBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RichTextFieldBlock


class StreamFieldUUIDFactory(wagtail_factories.StreamFieldFactory):
    def generate(self, *args, **kwargs):
        blocks = super().generate(*args, **kwargs)
        ret_val = list()
        # Convert to JSON so we can add id before create
        for block_name, value in blocks:
            block = self.factories[block_name]._meta.model()
            value = block.get_prep_value(value)
            ret_val.append({'type': block_name, 'value': value, 'id': str(uuid.uuid4())})
        return json.dumps(ret_val)


CustomFormFieldsFactory = StreamFieldUUIDFactory({
    'title': TitleBlockFactory,
    'email': EmailBlockFactory,
    'full_name': FullNameBlockFactory,
    'char': CharFieldBlockFactory,
    'number': NumberFieldBlockFactory,
    'radios': RadioFieldBlockFactory,
    'rich_text': RichTextFieldBlockFactory,
})
