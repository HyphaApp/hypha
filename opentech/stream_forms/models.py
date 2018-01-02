from collections import OrderedDict

from wagtail.wagtailforms.models import AbstractForm

from .blocks import FormFieldBlock
from .forms import BlockFieldWrapper, StreamBaseForm


class AbstractStreamForm(AbstractForm):
    class Meta:
        abstract = True

    def get_defined_fields(self):
        return self.form_fields

    def get_form_fields(self):
        form_fields = OrderedDict()
        field_blocks = self.get_defined_fields()
        for struct_child in field_blocks:
            block = struct_child.block
            struct_value = struct_child.value
            if isinstance(block, FormFieldBlock):
                field_name = block.get_slug(struct_value)
                form_fields[field_name] = block.get_field(struct_value)
            else:
                form_fields[struct_child.id] = BlockFieldWrapper(struct_child)
        return form_fields

    def get_form_class(self):
        return type('WagtailStreamForm', (StreamBaseForm,), self.get_form_fields())
