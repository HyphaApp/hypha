from opentech.apply.stream_forms.testing.factories import FormFieldBlockFactory
from opentech.apply.utils.blocks import RichTextFieldBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = RichTextFieldBlock
