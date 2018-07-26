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
        for struct_child in field_blocks:
            block = struct_child.block
            struct_value = struct_child.value
            if isinstance(block, FormFieldBlock):
                form_fields[struct_child.id] = block.get_field(struct_value)
            else:
                form_fields[struct_child.id] = BlockFieldWrapper(struct_child)
        return form_fields

    def get_form_class(self):
        return type('WagtailStreamForm', (self.submission_form_class,), self.get_form_fields())


class AbstractStreamForm(BaseStreamForm, AbstractForm):
    class Meta:
        abstract = True
