from django.utils.safestring import mark_safe
from django.core.files import File

from opentech.apply.stream_forms.blocks import (
    FileFieldBlock, FormFieldBlock, GroupToggleBlock, ImageFieldBlock, MultiFileFieldBlock
)
from opentech.apply.utils.blocks import SingleIncludeMixin

from opentech.apply.stream_forms.blocks import UploadableMediaBlock
from opentech.apply.utils.storage import PrivateStorage

from ..files import SubmissionStreamFieldFile

__all__ = ['AccessFormData']


class UnusedFieldException(Exception):
    pass


class AccessFormData:
    """Mixin for interacting with form data from streamfields

    requires:
         - form_data > jsonfield containing the submitted data
         - form_fields > streamfield containing the original form fields
    """
    stream_file_class = SubmissionStreamFieldFile
    storage_class = PrivateStorage

    @property
    def raw_data(self):
        # Returns the data mapped by field id instead of the data stored using the must include
        # values
        data = self.form_data.copy()
        for field_name, field_id in self.named_blocks.items():
            if field_id not in data:
                try:
                    response = data.pop(field_name)
                except KeyError:
                    # There was no value supplied for the named field
                    pass
                else:
                    data[field_id] = response
        return data

    @classmethod
    def stream_file(cls, instance, field, file):
        if not file:
            return []
        if isinstance(file, cls.stream_file_class):
            return file
        if isinstance(file, File):
            return cls.stream_file_class(instance, field, file, name=file.name, storage=cls.storage_class())

        # This fixes a backwards compatibility issue with #507
        # Once every application has been re-saved it should be possible to remove it
        if 'path' in file:
            file['filename'] = file['name']
            file['name'] = file['path']
        return cls.stream_file_class(instance, field, None, name=file['name'], filename=file.get('filename'), storage=cls.storage_class())

    @classmethod
    def process_file(cls, instance, field, file):
        if isinstance(file, list):
            return [cls.stream_file(instance, field, f) for f in file]
        else:
            return cls.stream_file(instance, field, file)

    def process_file_data(self, data):
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                file = self.process_file(self, field, data.get(field.id, []))
                try:
                    file.save()
                except AttributeError:
                    for f in file:
                        f.save()
                self.form_data[field.id] = file

    def extract_files(self):
        files = {}
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                files[field.id] = self.data(field.id) or []
                self.form_data.pop(field.id, None)
        return files

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        if 'form_data' in field_names:
            # When the form_data is loaded from the DB deserialise it
            instance.form_data = cls.deserialised_data(instance, instance.form_data, instance.form_fields)
        return instance

    @classmethod
    def deserialised_data(cls, instance, data, form_fields):
        # Converts the file dicts into actual file objects
        data = data.copy()
        # PERFORMANCE NOTE:
        # Do not attempt to iterate over form_fields - that will fully instantiate the form_fields
        # including any sub queries that they do
        for i, field_data in enumerate(form_fields.stream_data):
            block = form_fields.stream_block.child_blocks[field_data['type']]
            if isinstance(block, UploadableMediaBlock):
                field_id = field_data.get('id')
                if field_id:
                    field = form_fields[i]
                    file = data.get(field_id, [])
                    data[field_id] = cls.process_file(instance, field, file)
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
    def file_field_ids(self):
        for field_id, field in self.fields.items():
            if isinstance(field.block, (FileFieldBlock, ImageFieldBlock, MultiFileFieldBlock)):
                yield field_id

    @property
    def question_text_field_ids(self):
        file_fields = list(self.file_field_ids)
        for field_id, field in self.fields.items():
            if field_id in file_fields:
                pass
            elif isinstance(field.block, FormFieldBlock):
                yield field_id

    @property
    def first_group_question_text_field_ids(self):
        file_fields = list(self.file_field_ids)
        for field_id, field in self.fields.items():
            if field_id in file_fields:
                continue
            elif isinstance(field.block, GroupToggleBlock):
                break
            elif isinstance(field.block, FormFieldBlock):
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

    @property
    def normal_blocks(self):
        return [
            field_id
            for field_id in self.question_field_ids
            if field_id not in self.named_blocks
        ]

    @property
    def group_toggle_blocks(self):
        for field_id, field in self.fields.items():
            if isinstance(field.block, GroupToggleBlock):
                yield field_id, field

    @property
    def first_group_normal_text_blocks(self):
        return [
            field_id
            for field_id in self.first_group_question_text_field_ids
            if field_id not in self.named_blocks
        ]

    def serialize(self, field_id):
        field = self.field(field_id)
        data = self.data(field_id)
        return field.render(context={
            'serialize': True,
            'data': data,
        })

    def render_answer(self, field_id, include_question=False):
        try:
            field = self.field(field_id)
        except UnusedFieldException:
            return '-'
        data = self.data(field_id)
        # Some migrated content have empty address.
        if not data:
            return '-'
        return field.render(context={'data': data, 'include_question': include_question})

    def render_answers(self):
        # Returns a list of the rendered answers
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.normal_blocks
        ]

    def render_first_group_text_answers(self):
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.first_group_normal_text_blocks
        ]

    def render_text_blocks_answers(self):
        # Returns a list of the rendered answers of type text
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.question_text_field_ids
            if field_id not in self.named_blocks
        ]

    def output_answers(self):
        # Returns a safe string of the rendered answers
        return mark_safe(''.join(self.render_answers()))

    def output_text_answers(self):
        return mark_safe(''.join(self.render_text_blocks_answers()))

    def output_first_group_text_answers(self):
        return mark_safe(''.join(self.render_first_group_text_answers()))
