from django.forms.forms import DeclarativeFieldsMetaclass

from wagtail.wagtailforms.forms import BaseForm


class MixedFieldMetaclass(DeclarativeFieldsMetaclass):
    """Stores all fields passed to the class and not just the field type.
    This allows the form to be rendered when Field-like blocks are passed
    in as part of the definition
    """
    def __new__(mcs, name, bases, attrs):
        display = attrs.copy()
        new_class = super(MixedFieldMetaclass, mcs).__new__(mcs, name, bases, attrs)
        new_class.display = display
        return new_class


class StreamBaseForm(BaseForm, metaclass=MixedFieldMetaclass):
    def swap_fields_for_display(func):
        def wrapped(self, *args, **kwargs):
            # Replaces the form fields with the display fields
            # should only add new streamblocks and wont affect validation
            fields = self.fields.copy()
            self.fields = self.display
            yield from func(self, *args, **kwargs)
            self.fields = fields
        return wrapped

    @swap_fields_for_display
    def __iter__(self):
        yield from super().__iter__()

    @swap_fields_for_display
    def _html_output(self, *args, **kwargs):
        return super()._html_output(*args, **kwargs)


class BlockFieldWrapper:
    """Wraps stream blocks so that they can be rendered as a field within a form"""
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
