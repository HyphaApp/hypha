from collections import OrderedDict

from django.forms.forms import BaseForm, DeclarativeFieldsMetaclass
from django.forms.fields import Field

from wagtail.wagtailforms.models import AbstractForm

from .blocks import FormFieldBlock

class MixedFieldMetaclass(DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        display = attrs.copy()
        new_class = super(MixedFieldMetaclass, mcs).__new__(mcs, name, bases, attrs)
        new_class.display = display
        return new_class


class StreamBaseForm(BaseForm, metaclass=MixedFieldMetaclass):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')

        self.user = kwargs.pop('user', None)
        self.page = kwargs.pop('page', None)

        super().__init__(*args, **kwargs)

    def _html_output(self, *args, **kwargs):
        fields = self.fields.copy()
        self.fields = self.display
        render = super()._html_output(*args, **kwargs)
        self.fields = fields
        return render


class BlockFieldWrapper:
    is_hidden = False
    label = None
    help_text = None
    def __init__(self, block):
        self.block = block

    def get_bound_field(self, *args, **kwargs):
        return self

    def css_classes(self):
        return list()

    @property
    def errors(self):
        return list()

    @property
    def html_name(self):
        return self.block.id

    def __str__(self):
        return str(self.block.value)


class AbstractStreamForm(AbstractForm):
    class Meta:
        abstract = True

    def get_form_fields(self):
        form_fields = OrderedDict()
        field_blocks = self.form_fields
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
