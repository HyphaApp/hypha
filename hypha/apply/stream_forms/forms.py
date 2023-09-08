from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms.fields import EmailField
from django.forms.forms import DeclarativeFieldsMetaclass
from django.utils.safestring import mark_safe
from django_file_form.forms import FileFormMixin
from wagtail.contrib.forms.forms import BaseForm

from hypha.apply.users.utils import get_user_by_email, is_user_already_registered


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


class StreamBaseForm(FileFormMixin, forms.Form, metaclass=MixedFieldMetaclass):
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

    def hidden_fields(self):
        # No hidden fields are returned by default because of MixedFieldMetaclass
        return [self[f] for f in self.fields.keys() if self[f].is_hidden]

    def _update_files_data(self):
        """
        Overridden method of django_file_form's FileFormMixin, to handle multiple forms on the same page.
        """
        # handle two form_id, use case PAF and SOW
        form_id = self.data.getlist(self.add_prefix("form_id"))

        if not form_id:
            return

        form_id = form_id[0]
        for field_name in self._file_form_field_names():
            field = self.fields[field_name]
            prefixed_field_name = self.add_prefix(field_name)

            file_data = field.get_file_data(prefixed_field_name, form_id)

            if file_data:
                # NB: django-formtools wizard uses dict instead of MultiValueDict
                if isinstance(file_data, list) and hasattr(self.files, "setlist"):
                    self.files.setlist(prefixed_field_name, file_data)
                else:
                    self.files[prefixed_field_name] = file_data

    def delete_temporary_files(self):
        """
        Overridden method of django_file_form's FileFormMixin, to handle multiple forms on the same page.
        """
        form_id = self.data.getlist(self.add_prefix("form_id"))

        if not form_id:
            return

        form_id = form_id[0]
        for field_name, field in self.fields.items():
            if hasattr(field, "delete_file_data"):
                prefixed_field_name = self.add_prefix(field_name)
                field.delete_file_data(prefixed_field_name, form_id)


class PageStreamBaseForm(BaseForm, StreamBaseForm):
    """Adds page and user reference to the form class"""

    def clean(self):
        cleaned_data = super().clean()
        for field, value in self.fields.items():
            # email validation of submission form
            if isinstance(value, EmailField):
                email = self.data.get(field)
                if email:
                    is_registered, _ = is_user_already_registered(
                        email=self.data.get(field)
                    )
                    if is_registered:
                        user = get_user_by_email(email=email)
                        if not user:
                            self.add_error(field, "Found multiple account")
                            raise ValidationError(
                                mark_safe(
                                    "Found multiple account for the same email. "
                                    "Please login with the correct credentials or "
                                    '<a href="mailto:{}">'
                                    "contact to the support team"
                                    "</a>.".format(settings.ORG_EMAIL)
                                )
                            )

                        elif not user.is_active:
                            self.add_error(field, "Found an inactive account")
                            raise ValidationError(
                                mark_safe(
                                    "Found an inactive account for the same email. "
                                    "Please use different email or "
                                    '<a href="mailto:{}">'
                                    "contact to the support team"
                                    "</a>.".format(settings.ORG_EMAIL)
                                )
                            )

        return cleaned_data


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
        return []

    @property
    def errors(self):
        return []

    @property
    def html_name(self):
        return self.block.id

    def __str__(self):
        return str(self.block.value)
