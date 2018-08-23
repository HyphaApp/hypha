from collections import defaultdict
import json
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile

import factory
from wagtail.core.blocks import RichTextBlock
from wagtail.core.rich_text import RichText
import wagtail_factories

from opentech.apply.stream_forms import blocks as stream_blocks

__all__ = ['FormFieldBlockFactory', 'CharFieldBlockFactory',
           'NumberFieldBlockFactory', 'RadioFieldBlockFactory',
           'UploadableMediaFactory', 'ImageFieldBlockFactory',
           'FileFieldBlockFactory', 'MultiFileFieldBlockFactory']


class AnswerFactory(factory.Factory):
    def _create(self, *args, sub_factory=None, **kwargs):
        return sub_factory.make_answer(kwargs)

    def _build(self, *args, sub_factory=None, **kwargs):
        return sub_factory.make_answer(kwargs)


class AddFormFieldsMetaclass(factory.base.FactoryMetaClass):
    def __new__(mcs, class_name, bases, attrs):
        # Add the form field definitions to allow nested calls
        field_factory = attrs.pop('field_factory', None)
        if field_factory:
            wrapped_factories = {
                k: factory.SubFactory(AnswerFactory, sub_factory=v)
                for k, v in field_factory.factories.items()
                if issubclass(v, FormFieldBlockFactory)
            }
            attrs.update(wrapped_factories)
        return super().__new__(mcs, class_name, bases, attrs)


class FormDataFactory(factory.Factory, metaclass=AddFormFieldsMetaclass):
    @classmethod
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

    @classmethod
    def _build(self, *args, **kwargs):
        return self._create(*args, **kwargs)


class ParagraphBlockFactory(wagtail_factories.blocks.BlockFactory):
    class Meta:
        model = RichTextBlock

    @classmethod
    def _create(cls, model_class, value):
        value = RichText(value)
        return super()._create(model_class, value)


class FormFieldBlockFactory(wagtail_factories.StructBlockFactory):
    default_value = factory.Faker('sentence')
    field_label = factory.Faker('sentence')
    help_text = factory.LazyAttribute(lambda o: str(o._Resolver__step.builder.factory_meta.model))

    class Meta:
        model = stream_blocks.FormFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return cls.default_value.generate(params)

    @classmethod
    def make_form_answer(cls, params=dict()):
        return cls.make_answer(params)


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
        params = params.copy()
        params.setdefault('data', b'this is some content')
        file_name, file = cls.default_value()._make_content(params)
        return InMemoryUploadedFile(file, 'file', file_name, None, file.tell(), None)


class ImageFieldBlockFactory(UploadableMediaFactory):
    default_value = factory.django.ImageField

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
    def generate(self, step, params):
        params = self.build_form(params)
        blocks = super().generate(step, params)
        ret_val = list()
        # Convert to JSON so we can add id before create
        for block_name, value in blocks:
            block = self.factories[block_name]._meta.model()
            value = block.get_prep_value(value)
            ret_val.append({'type': block_name, 'value': value, 'id': str(uuid.uuid4())})
        return json.dumps(ret_val)

    def build_form(self, data):
        extras = defaultdict(dict)
        exclusions = []
        for field, value in data.items():
            # we dont care about position
            name, attr = field.split('__')
            if name == 'exclude':
                exclusions.append(attr)
            else:
                extras[name] = {attr: value}


        form_fields = {}
        for i, field in enumerate(self.factories):
            if field == 'text_markup' or field in exclusions:
                pass
            else:
                form_fields[f'{i}__{field}__'] = ''
            for attr, value in extras[field].items():
                form_fields[f'{i}__{field}__{attr}'] = value

        return form_fields

    def form_response(self, fields, field_values=dict()):
        data = {
            field.id: self.factories[field.block.name].make_form_answer(field_values.get(field, {}))
            for field in fields
            if hasattr(self.factories[field.block.name], 'make_form_answer')
        }
        return flatten_for_form(data)


def flatten_for_form(data, field_name='', number=False):
    result = {}
    for i, (field, value) in enumerate(data.items()):
        if number:
            field = f'{field_name}_{i}'
        if isinstance(value, dict):
            result.update(**flatten_for_form(value, field_name=field, number=True))
        else:
            result[field] = value
    return result
