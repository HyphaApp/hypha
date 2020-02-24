from hypha.apply.stream_forms.testing.factories import FormFieldBlockFactory
from hypha.apply.utils.blocks import RichTextFieldBlock


class RichTextFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = RichTextFieldBlock
