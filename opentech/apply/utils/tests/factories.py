from opentech.apply.stream_forms.tests.factories import FormFieldBlockFactory
from opentech.apply.utils.blocks import RichTextFieldBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = RichTextFieldBlock
