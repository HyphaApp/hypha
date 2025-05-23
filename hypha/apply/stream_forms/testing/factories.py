import json
import uuid
from collections import defaultdict

import factory
import wagtail_factories
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.serializers.json import DjangoJSONEncoder
from wagtail.blocks import RichTextBlock, StructValue
from wagtail.rich_text import RichText

from hypha.apply.stream_forms import blocks as stream_blocks

__all__ = [
    "BLOCK_FACTORY_DEFINITION",
    "FormFieldBlockFactory",
    "CharFieldBlockFactory",
    "NumberFieldBlockFactory",
    "RadioFieldBlockFactory",
    "UploadableMediaFactory",
    "ImageFieldBlockFactory",
    "FileFieldBlockFactory",
    "MultiFileFieldBlockFactory",
]


class AnswerFactory(factory.Factory):
    def _create(self, *args, sub_factory=None, **kwargs):
        return sub_factory.make_answer(kwargs)

    def _build(self, *args, sub_factory=None, **kwargs):
        return sub_factory.make_answer(kwargs)


class AddFormFieldsMetaclass(factory.base.FactoryMetaClass):
    def __new__(mcs, class_name, bases, attrs):
        # Add the form field definitions to allow nested calls
        field_factory = attrs.pop("field_factory", None)
        if field_factory:
            # Check if stream_block_factory is a class and use class attributes instead of `items()`
            stream_block_factories = getattr(
                field_factory, "stream_block_factory", None
            )
            if stream_block_factories:
                # Access stream block factory attributes via __dict__ or similar mechanism
                stream_blocks = {
                    k: v.get_factory()
                    for k, v in stream_block_factories.__dict__.items()
                    if isinstance(v, factory.SubFactory)
                }
                wrapped_factories = {
                    k: factory.SubFactory(AnswerFactory, sub_factory=v)
                    for k, v in stream_blocks.items()
                    if issubclass(v, FormFieldBlockFactory)
                }
                attrs.update(wrapped_factories)
        return super().__new__(mcs, class_name, bases, attrs)


class FormDataFactory(factory.Factory, metaclass=AddFormFieldsMetaclass):
    @classmethod
    def _create(cls, *args, form_fields=None, for_factory=None, clean=False, **kwargs):
        if form_fields is None:
            form_fields = {}

        if form_fields and isinstance(form_fields, str):
            form_fields = json.loads(form_fields)
            form_definition = {field["type"]: field["id"] for field in form_fields}
        else:
            form_definition = {
                f.block_type: f.id
                for f in form_fields
                or for_factory.Meta.model.form_fields.field.to_python(form_fields)
            }

        form_data = {}
        for name, answer in kwargs.items():
            try:
                key = form_definition[name]
            except KeyError:
                # We are not using that field - don't add the submission data
                pass
            else:
                form_data[key] = answer

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
    default_value = factory.Faker("sentence")
    field_label = factory.Faker("sentence")
    help_text = factory.LazyAttribute(
        lambda o: RichText(
            f"Help text for {o._Resolver__step.builder.factory_meta.model.__name__}"
        )
    )

    class Meta:
        model = stream_blocks.FormFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        params = params or {}
        return cls.default_value.evaluate(None, None, dict(params, locale=None))

    @classmethod
    def make_form_answer(cls, params=None):
        if params:
            return params
        return cls.make_answer(params or {})


class CharFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker("sentence")

    class Meta:
        model = stream_blocks.CharFieldBlock


class TextFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker("sentence")

    class Meta:
        model = stream_blocks.TextFieldBlock


class DateFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.Faker("date_object")

    class Meta:
        model = stream_blocks.DateFieldBlock


class TimeFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.LazyFunction(
        lambda: factory.Faker("time_object")
        .evaluate(None, None, {"locale": None})
        .replace(microsecond=0)
    )

    class Meta:
        model = stream_blocks.TimeFieldBlock


class DateTimeFieldBlockFactory(FormFieldBlockFactory):
    default_value = factory.LazyFunction(
        lambda: factory.Faker("date_time")
        .evaluate(None, None, {"locale": None})
        .replace(microsecond=0)
    )

    class Meta:
        model = stream_blocks.DateTimeFieldBlock

    @classmethod
    def make_form_answer(cls, params=None):
        if params:
            date_time = params
        else:
            date_time = super().make_form_answer(params)
        return {
            "date": str(date_time.date()),
            "time": str(date_time.time().replace(microsecond=0)),
        }


class NumberFieldBlockFactory(FormFieldBlockFactory):
    default_value = 100

    class Meta:
        model = stream_blocks.NumberFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        return cls.default_value


class CheckboxFieldBlockFactory(FormFieldBlockFactory):
    choices = ["check_one", "check_two"]

    class Meta:
        model = stream_blocks.CheckboxFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        return cls.choices[0]


class CheckboxesFieldBlockFactory(FormFieldBlockFactory):
    checkboxes = ["check_multiple_one", "check_multiple_two", "check_multiple_three"]

    class Meta:
        model = stream_blocks.CheckboxesFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        return cls.checkboxes[0:2]


class RadioFieldBlockFactory(FormFieldBlockFactory):
    choices = ["first", "second"]

    class Meta:
        model = stream_blocks.RadioButtonsFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        return cls.choices[0]


class DropdownFieldBlockFactory(FormFieldBlockFactory):
    choices = ["first", "second"]

    class Meta:
        model = stream_blocks.DropdownFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        return cls.choices[0]


class UploadableMediaFactory(FormFieldBlockFactory):
    default_value = factory.django.FileField()

    @classmethod
    def make_answer(cls, params=None):
        params = params or {}
        params.setdefault("data", b"this is some content")
        if params.get("filename") is None:
            params["filename"] = "test_example.pdf"
        file_name, file = cls.default_value._make_content(params)
        return SimpleUploadedFile(file_name, file.read())


class ImageFieldBlockFactory(UploadableMediaFactory):
    default_value = factory.django.ImageField()

    class Meta:
        model = stream_blocks.ImageFieldBlock


class FileFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.FileFieldBlock


class MultiFileFieldBlockFactory(UploadableMediaFactory):
    class Meta:
        model = stream_blocks.MultiFileFieldBlock

    @classmethod
    def make_answer(cls, params=None):
        return [UploadableMediaFactory.make_answer() for _ in range(2)]


class StreamFieldUUIDFactory(wagtail_factories.StreamFieldFactory):
    def evaluate(self, instance, step, extra):
        params = self.build_form(extra)
        blocks = super().evaluate(instance, step, params)
        ret_val = []
        factories = {
            k: v.get_factory()
            for k, v in self.stream_block_factory.__dict__.items()
            if isinstance(v, factory.SubFactory)
        }
        # Convert to JSON so we can add id before create
        for block_name, value in blocks:
            block = factories[block_name]._meta.model()

            value = block.get_prep_value(self.filtered_child_block_value(block, value))
            ret_val.append(
                {"type": block_name, "value": value, "id": str(uuid.uuid4())}
            )
        return json.dumps(ret_val, cls=DjangoJSONEncoder)

    def build_form(self, data):
        extras = defaultdict(dict)
        exclusions = []
        multiples = {}
        for field, value in data.items():
            # we dont care about position
            name, attr = field.split("__")
            if name == "exclude":
                exclusions.append(attr)
            elif name == "multiple":
                multiples[attr] = value
            else:
                extras[name] = {attr: value}

        defined_both = set(exclusions) & set(multiples)
        if defined_both:
            raise ValueError(
                "Cant exclude and provide multiple at the same time: {}".format(
                    ", ".join(defined_both)
                )
            )

        form_fields = {}
        field_count = 0
        stream_blocks = {
            k: v.get_factory()
            for k, v in self.stream_block_factory.__dict__.items()
            if isinstance(v, factory.SubFactory)
        }
        for field in stream_blocks:
            if field == "text_markup" or field in exclusions or not field:
                pass
            else:
                for _ in range(multiples.get(field, 1)):
                    form_fields[f"{field_count}__{field}__"] = ""
                    field_count += 1
            if extras[field]:
                for attr, value in extras[field].items():
                    form_fields[f"{field_count}__{field}__{attr}"] = value
                field_count += 1

        return form_fields

    def filtered_child_block_value(self, block, value):
        filtered_value = value
        if isinstance(value, StructValue):
            filtered_value = {
                key: val for key, val in value.items() if key in block.child_blocks
            }
        return filtered_value

    def form_response(self, fields, field_values=None):
        if not field_values:
            field_values = {}
        stream_blocks = {
            k: v.get_factory()
            for k, v in self.stream_block_factory.__dict__.items()
            if isinstance(v, factory.SubFactory)
        }
        data = {
            field.id: stream_blocks[field.block.name].make_form_answer(
                field_values.get(field.id, {})
            )
            for field in fields
            if hasattr(stream_blocks[field.block.name], "make_form_answer")
        }
        return flatten_for_form(data)


NON_FILE_BLOCK_FACTORY_DEFINITION = {
    "text_markup": factory.SubFactory(ParagraphBlockFactory),
    "char": factory.SubFactory(CharFieldBlockFactory),
    "text": factory.SubFactory(TextFieldBlockFactory),
    "number": factory.SubFactory(NumberFieldBlockFactory),
    "checkbox": factory.SubFactory(CheckboxFieldBlockFactory),
    "radios": factory.SubFactory(RadioFieldBlockFactory),
    "dropdown": factory.SubFactory(DropdownFieldBlockFactory),
    "checkboxes": factory.SubFactory(CheckboxesFieldBlockFactory),
    "date": factory.SubFactory(DateFieldBlockFactory),
    "time": factory.SubFactory(TimeFieldBlockFactory),
    "datetime": factory.SubFactory(DateTimeFieldBlockFactory),
}

BLOCK_FACTORY_DEFINITION = {
    **NON_FILE_BLOCK_FACTORY_DEFINITION,
    "image": factory.SubFactory(ImageFieldBlockFactory),
    "file": factory.SubFactory(FileFieldBlockFactory),
    "multi_file": factory.SubFactory(MultiFileFieldBlockFactory),
}

# There are two here, because some tests will fail due to JSON serialization errors
# if SimpleUploadedFile is included in the factory (most notably Project ReportVersion tests)
NonFileFormFieldsBlockFactory = StreamFieldUUIDFactory(
    NON_FILE_BLOCK_FACTORY_DEFINITION
)
FormFieldsBlockFactory = StreamFieldUUIDFactory(BLOCK_FACTORY_DEFINITION)


def flatten_for_form(data, field_name="", number=False):
    result = {}
    for i, (field, value) in enumerate(data.items()):
        if number:
            field = f"{field_name}_{i}"
        if isinstance(value, dict):
            result.update(**flatten_for_form(value, field_name=field, number=True))
        else:
            result[field] = value
    return result
