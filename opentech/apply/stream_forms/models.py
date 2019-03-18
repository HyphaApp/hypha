# Credit to https://github.com/BertrandBordage for initial implementation
from collections import OrderedDict

from wagtail.contrib.forms.models import AbstractForm

from .blocks import FormFieldBlock
from .forms import BlockFieldWrapper, PageStreamBaseForm


class BaseStreamForm:
    submission_form_class = PageStreamBaseForm

    def get_defined_fields(self):
        return self.form_fields

    def get_form_fields(self):
        form_fields = OrderedDict()
        field_blocks = self.get_defined_fields()
        group_counter = 1
        for struct_child in field_blocks:
            block = struct_child.block
            struct_value = struct_child.value

            if isinstance(block, FormFieldBlock):
                field_from_block = block.get_field(struct_value)
                field_from_block.group = group_counter
                form_fields[struct_child.id] = field_from_block
            elif struct_child.block_type != 'group':
                field_wrapper = BlockFieldWrapper(struct_child)
                field_wrapper.group = group_counter
                form_fields[struct_child.id] = field_wrapper
            else:
                group_counter += 1

        return form_fields

    def get_form_class(self):
        return type('WagtailStreamForm', (self.submission_form_class,), self.get_form_fields())


class AbstractStreamForm(BaseStreamForm, AbstractForm):
    class Meta:
        abstract = True
