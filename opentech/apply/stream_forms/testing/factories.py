import json
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile

import factory
from wagtail.core.blocks import CharBlock
import wagtail_factories

from opentech.apply.stream_forms import blocks as stream_blocks

__all__ = ['CharBlockFactory', 'FormFieldBlockFactory', 'CharFieldBlockFactory', 'NumberFieldBlockFactory',
           'RadioFieldBlockFactory', 'UploadableMediaFactory', 'ImageFieldBlockFactory', 'FileFieldBlockFactory',
           'MultiFileFieldBlockFactory']


class AnswerFactory(factory.Factory):
    def _create(self, *args, sub_factory=None, **kwargs):
        return sub_factory.make_answer(kwargs)


class AddFormFieldsMetaclass(factory.base.FactoryMetaClass):
    def __new__(mcs, class_name, bases, attrs):
        # Add the form field definitions to allow nested calls
        field_factory = attrs.pop('field_factory', None)
        if field_factory:
            wrapped_factories = {
                k: factory.SubFactory(AnswerFactory, sub_factory=v)
                for k, v in field_factory.factories.items()
            }
            attrs.update(wrapped_factories)
        return super().__new__(mcs, class_name, bases, attrs)


class FormDataFactory(factory.Factory, metaclass=AddFormFieldsMetaclass):
    def _create(self, *args, form_fields={}, for_factory=None, clean=False, **kwargs):
        if form_fields and isinstance(form_fields, str):
            form_fields = json.loads(form_fields)
            form_definition = {
                field['type']: field['id']
                for field in form_fields
            }
        else:
            form_definition = {
                f.block_type: f.id
                for f in form_fields or for_factory.Meta.model.form_fields.field.to_python(form_fields)
            }

        form_data = {}
        for name, answer in kwargs.items():
            form_data[form_definition[name]] = answer

        if clean:
            clean_object = for_factory()
            clean_object.form_fields = form_fields
            clean_object.form_data = form_data
            clean_object.save()
            form_data = clean_object.form_data.copy()
            clean_object.delete()
            return form_data

        return form_data


class CharBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = CharBlock


class FormFieldBlockFactory(wagtail_factories.StructBlockFactory):
    default_value = factory.Faker('word')

    class Meta:
        model = stream_blocks.FormFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.default_value.generate(params)


class CharFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker('sentence')

    class Meta:
        model = stream_blocks.CharFieldBlock


class NumberFieldBlockFactory(FormFieldBlockFactory):
    default_value = 100

    class Meta:
        model = stream_blocks.NumberFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.default_value


class RadioFieldBlockFactory(FormFieldBlockFactory):
    choices = ['first', 'second']

    class Meta:
        model = stream_blocks.RadioButtonsFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.choices[0]


class UploadableMediaFactory(FormFieldBlockFactory):
    default_value = factory.django.FileField

    @classmethod
    def make_answer(cls, params=dict()):
        file_name, file = cls.default_value()._make_content(params)
        return InMemoryUploadedFile(file, 'file', file_name, None, file.tell(), None)


class ImageFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.ImageFieldBlock


class FileFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.FileFieldBlock


class MultiFileFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.MultiFileFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return [UploadableMediaFactory.make_answer() for _ in range(2)]


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
