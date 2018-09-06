from django.conf import settings
from django.utils.text import mark_safe
from django.core.files import File
from django.core.files.storage import get_storage_class

from opentech.apply.stream_forms.blocks import FormFieldBlock
from opentech.apply.utils.blocks import MustIncludeFieldBlock

from opentech.apply.stream_forms.blocks import UploadableMediaBlock
from opentech.apply.stream_forms.files import StreamFieldFile


__all__ = ['AccessFormData']


submission_storage = get_storage_class(getattr(settings, 'PRIVATE_FILE_STORAGE', None))()


class AccessFormData:
    """Mixin for interacting with form data from streamfields

    requires:
         - form_data > jsonfield containing the submitted data
         - form_fields > streamfield containing the original form fields

    """

    @property
    def raw_data(self):
        # Returns the data mapped by field id instead of the data stored using the must include
        # values
        data = self.form_data.copy()
        for field_name, field_id in self.must_include.items():
            if field_id not in data:
                response = data[field_name]
                data[field_id] = response
        return data

    @classmethod
    def stream_file(cls, file):
        if isinstance(file, StreamFieldFile):
            return file
        if isinstance(file, File):
            return StreamFieldFile(file.file, name=file.name, storage=submission_storage)
        return StreamFieldFile(None, name=file['name'], filename=file.get('filename'), storage=submission_storage)

    @classmethod
    def process_file(cls, file):
        try:
            return cls.stream_file(file)
        except TypeError:
            return [cls.stream_file(f) for f in file]

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        if 'form_data' in field_names:
            # When the form_data is loaded from the DB deserialise it
            instance.form_data = cls.deserialised_data(instance.form_data, instance.form_fields)
        return instance

    @classmethod
    def deserialised_data(cls, data, form_fields):
        # Converts the file dicts into actual file objects
        data = data.copy()
        for field in form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                file = data.get(field.id, [])
                data[field.id] = cls.process_file(file)
        return data

    def get_definitive_id(self, id):
        if id in self.must_include:
            return self.must_include[id]
        return id

    def field(self, id):
        definitive_id = self.get_definitive_id(id)
        return self.raw_fields[definitive_id]

    def data(self, id):
        definitive_id = self.get_definitive_id(id)
        try:
            return self.raw_data[definitive_id]
        except KeyError as e:
            # We have most likely progressed application forms so the data isnt in form_data
            return None

    @property
    def question_field_ids(self):
        for field_id, field in self.fields.items():
            if isinstance(field.block, FormFieldBlock):
                yield field_id

    @property
    def raw_fields(self):
        # Field ids to field class mapping - similar to raw_data
        return {
            field.id: field
            for field in self.form_fields
        }

    @property
    def fields(self):
        # ALl fields on the application
        fields = self.raw_fields.copy()
        for field_name, field_id in self.must_include.items():
            response = fields.pop(field_id)
            fields[field_name] = response
        return fields

    @property
    def must_include(self):
        return {
            field.block.name: field.id
            for field in self.form_fields
            if isinstance(field.block, MustIncludeFieldBlock)
        }

    def render_answer(self, field_id, include_question=False):
        field = self.field(field_id)
        data = self.data(field_id)
        return field.render(context={'data': data, 'include_question': include_question})

    def render_answers(self):
        # Returns a list of the rendered answers
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.question_field_ids
            if field_id not in self.must_include
        ]

    def output_answers(self):
        # Returns a safe string of the rendered answers
        return mark_safe(''.join(self.render_answers()))
