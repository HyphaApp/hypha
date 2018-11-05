from django.conf import settings
from django.utils.text import mark_safe
from django.core.files import File
from django.core.files.storage import get_storage_class

from opentech.apply.stream_forms.blocks import FormFieldBlock
from opentech.apply.utils.blocks import SingleIncludeMixin

from opentech.apply.stream_forms.blocks import UploadableMediaBlock
from opentech.apply.stream_forms.files import StreamFieldFile


__all__ = ['AccessFormData']


submission_storage = get_storage_class(getattr(settings, 'PRIVATE_FILE_STORAGE', None))()


class UnusedFieldException(Exception):
    pass


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
        for field_name, field_id in self.named_blocks.items():
            if field_id not in data:
                try:
                    response = data[field_name]
                except KeyError:
                    # There was no value supplied for the named field
                    pass
                else:
                    data[field_id] = response
        return data

    @classmethod
    def stream_file(cls, file):
        if isinstance(file, StreamFieldFile):
            return file
        if isinstance(file, File):
            return StreamFieldFile(file, name=file.name, storage=submission_storage)

        # This fixes a backwards compatibility issue with #507
        # Once every application has been re-saved it should be possible to remove it
        if 'path' in file:
            file['filename'] = file['name']
            file['name'] = file['path']
        return StreamFieldFile(None, name=file['name'], filename=file.get('filename'), storage=submission_storage)

    @classmethod
    def process_file(cls, file):
        if isinstance(file, list):
            return [cls.stream_file(f) for f in file]
        else:
            return cls.stream_file(file)

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
        for field in form_fields.stream_data:
            block = form_fields.stream_block.child_blocks[field['type']]
            if isinstance(block, UploadableMediaBlock):
                field_id = field.get('id')
                file = data.get(field_id, [])
                data[field_id] = cls.process_file(file)
        return data

    def get_definitive_id(self, id):
        if id in self.named_blocks:
            return self.named_blocks[id]
        return id

    def field(self, id):
        definitive_id = self.get_definitive_id(id)
        try:
            return self.raw_fields[definitive_id]
        except KeyError:
            raise UnusedFieldException(id) from None

    def data(self, id):
        definitive_id = self.get_definitive_id(id)
        try:
            return self.raw_data[definitive_id]
        except KeyError:
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
        for field_name, field_id in self.named_blocks.items():
            response = fields.pop(field_id)
            fields[field_name] = response
        return fields

    @property
    def named_blocks(self):
        return {
            field.block.name: field.id
            for field in self.form_fields
            if isinstance(field.block, SingleIncludeMixin)
        }

    def render_answer(self, field_id, include_question=False):
        try:
            field = self.field(field_id)
        except UnusedFieldException:
            return '-'
        data = self.data(field_id)
        return field.render(context={'data': data, 'include_question': include_question})

    def render_answers(self):
        # Returns a list of the rendered answers
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.question_field_ids
            if field_id not in self.named_blocks
        ]

    def output_answers(self):
        # Returns a safe string of the rendered answers
        return mark_safe(''.join(self.render_answers()))
