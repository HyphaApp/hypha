import os

from django.core.files import File
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django_file_form.models import PlaceholderUploadedFile
from django_file_form.uploaded_file import S3UploadedFileWithId

from hypha.apply.stream_forms.blocks import (
    FileFieldBlock,
    FormFieldBlock,
    GroupToggleBlock,
    ImageFieldBlock,
    MultiFileFieldBlock,
    MultiInputCharFieldBlock,
    UploadableMediaBlock,
)
from hypha.apply.utils.blocks import SingleIncludeMixin
from hypha.apply.utils.storage import PrivateStorage

from ..files import PrivateStreamFieldFile

__all__ = ["AccessFormData"]


class UnusedFieldException(Exception):
    pass


class AccessFormData:
    """Mixin for interacting with form data from streamfields

    requires:
         - form_data > jsonfield containing the submitted data
         - form_fields > streamfield containing the original form fields
    """

    stream_file_class = PrivateStreamFieldFile
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
            # New content, never let its name point to a stored file path.
            return cls.stream_file_class(
                instance,
                field,
                file,
                name=os.path.basename(file.name),
                storage=cls.storage_class(),
            )

        if isinstance(file, PlaceholderUploadedFile):
            return cls.stream_file_class(
                instance,
                field,
                None,
                name=file.file_id,
                filename=file.name,
                storage=cls.storage_class(),
            )

        # This fixes a backwards compatibility issue with #507
        # Once every application has been re-saved it should be possible to remove it
        if "path" in file:
            file["filename"] = file["name"]
            file["name"] = file["path"]
        return cls.stream_file_class(
            instance,
            field,
            None,
            name=file["name"],
            filename=file.get("filename"),
            storage=cls.storage_class(),
        )

    @classmethod
    def process_file(cls, instance, field, file):
        if isinstance(file, list):
            return [cls.stream_file(instance, field, f) for f in file]
        else:
            return cls.stream_file(instance, field, file)

    def process_file_data(self, data, latest_existing_data=None):
        """
        Store new files and keep existing ones.

        Files already stored under the instance's own path are kept as they are,
        new uploads are always saved. Files kept in an edit form are posted back
        as placeholders, those are only accepted if they belong to the instance,
        i.e. are stored under its path or are in latest_existing_data.
        S3 direct uploads are not used and always dropped.
        """
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                # Only used by the file form, it should not be stored in form_data.
                self.form_data.pop(field.id + "-uploads", None)

                known_names = self._file_names(
                    (latest_existing_data or {}).get(field.id)
                )
                value = data.get(field.id, [])
                is_list = isinstance(value, list)
                files = []
                for file in value if is_list else [value]:
                    if isinstance(file, S3UploadedFileWithId):
                        # Hypha does not use S3 direct uploads, the S3 key is
                        # posted by the client and could point to any file.
                        continue
                    stream_file = self.stream_file(self, field, file)
                    if not stream_file:
                        continue
                    if (
                        isinstance(file, PlaceholderUploadedFile)
                        and not stream_file.is_own_file()
                        and stream_file.name not in known_names
                    ):
                        # The placeholder path is posted by the client, never
                        # trust it to point to a file of another instance.
                        continue
                    try:
                        stream_file.save()
                    except FileNotFoundError:
                        pass
                    files.append(stream_file)

                if is_list:
                    self.form_data[field.id] = files
                else:
                    self.form_data[field.id] = files[0] if files else []

    @staticmethod
    def _file_names(files):
        if not files:
            return set()
        files = files if isinstance(files, list) else [files]
        return {f.name if isinstance(f, File) else f.get("name") for f in files}

    def extract_files(self):
        files = {}
        for field in self.form_fields:
            if isinstance(field.block, UploadableMediaBlock):
                files[field.id] = self.data(field.id) or []
        return files

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        if "form_data" in field_names:
            # When the form_data is loaded from the DB deserialise it
            instance.form_data = cls.deserialised_data(
                instance, instance.form_data, instance.form_fields
            )
        return instance

    @classmethod
    def deserialised_data(cls, instance, data, form_fields):
        # Converts the file dicts into actual file objects
        data = data.copy()
        # PERFORMANCE NOTE:
        # Do not attempt to iterate over form_fields - that will fully instantiate the form_fields
        # including any sub queries that they do
        for i, field_data in enumerate(form_fields.raw_data):
            block = form_fields.stream_block.child_blocks[field_data["type"]]
            if isinstance(block, UploadableMediaBlock):
                field_id = field_data.get("id")
                if field_id:
                    # Left over in older form_data, it is only used by the file form.
                    data.pop(field_id + "-uploads", None)
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
            # We have most likely progressed application forms so the data isn't in form_data
            return None

    @property
    def question_field_ids(self):
        for field_id, field in self.fields.items():
            if isinstance(field.block, FormFieldBlock):
                yield field_id

    @property
    def file_field_ids(self):
        for field_id, field in self.fields.items():
            if isinstance(
                field.block, (FileFieldBlock, ImageFieldBlock, MultiFileFieldBlock)
            ):
                yield field_id

    @property
    def question_text_field_ids(self):
        file_fields = set(self.file_field_ids)
        for field_id, field in self.fields.items():
            if field_id not in file_fields and isinstance(field.block, FormFieldBlock):
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
        return {field.id: field for field in self.form_fields}

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

    def get_serialize_multi_inputs_answer(self, field):
        number_of_inputs = field.value.get("number_of_inputs")
        answers = [self.data(field.id + "_" + str(i)) for i in range(number_of_inputs)]
        data = ", ".join(filter(None, answers))
        return data

    def serialize(self, field_id):
        """Serialize a single answer.

        Never redacted: unlike `render_answer()` this does not consult `is_pii`,
        so everything reached through it is for staff-only views and exports.
        """
        field = self.field(field_id)
        if isinstance(field.block, MultiInputCharFieldBlock):
            data = self.get_serialize_multi_inputs_answer(field)
        else:
            data = self.data(field_id)
        return field.render(
            context={
                "serialize": True,
                "data": data,
            }
        )

    def get_multi_inputs_answer(
        self, field, include_question=False, show_pii_marker=False
    ):
        number_of_inputs = field.value.get("number_of_inputs")
        answers = [self.data(field.id + "_" + str(i)) for i in range(number_of_inputs)]

        render_data = [
            field.render(
                context={
                    "data": answer,
                    "include_question": include_question if i == 0 else False,
                    "show_pii_marker": show_pii_marker,
                }
            )
            for i, answer in enumerate(filter(None, answers))
        ]
        joined = "".join(render_data).replace("</section>", "")
        if include_question and render_data:
            return joined + "</section>"
        return joined

    @staticmethod
    def field_is_pii(field) -> bool:
        """Has this field been marked as containing personal information?"""
        try:
            return bool(field.value.get("is_pii"))
        except AttributeError:
            # Blocks such as text_markup hold a scalar rather than a StructValue.
            return False

    def render_answer(
        self, field_id, include_question=False, redact_pii=False, mark_pii=False
    ):
        try:
            field = self.field(field_id)
        except UnusedFieldException:
            return "-"
        is_pii = self.field_is_pii(field)
        if redact_pii and is_pii:
            return render_to_string(
                "stream_forms/render_redacted_field.html",
                {
                    "value": field.block.get_display_value(field.value),
                    "include_question": include_question,
                },
            )
        show_pii_marker = mark_pii and is_pii
        if isinstance(field.block, MultiInputCharFieldBlock):
            render_data = self.get_multi_inputs_answer(
                field, include_question, show_pii_marker
            )
            return render_data
        else:
            data = self.data(field_id)
        # Some migrated content have empty address.
        if not data:
            return field.render(
                context={
                    "data": "",
                    "include_question": include_question,
                    "show_pii_marker": show_pii_marker,
                }
            )
        return field.render(
            context={
                "data": data,
                "include_question": include_question,
                "show_pii_marker": show_pii_marker,
            }
        )

    def render_answers(self, redact_pii=False, mark_pii=False):
        # Returns a list of the rendered answers
        return [
            self.render_answer(
                field_id,
                include_question=True,
                redact_pii=redact_pii,
                mark_pii=mark_pii,
            )
            for field_id in self.normal_blocks
        ]

    def render_first_group_text_answers(self):
        """Render the text answers of the first group, never redacted.

        Answers marked as personal information are rendered in the clear, so
        only use this where the view is already restricted to staff.
        """
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.first_group_normal_text_blocks
        ]

    def render_text_blocks_answers(self):
        """Render the answers of type text, never redacted.

        Answers marked as personal information are rendered in the clear, so
        only use this where the view is already restricted to staff. Its one
        caller is the revision comparison view, which is `staff_required`.
        """
        return [
            self.render_answer(field_id, include_question=True)
            for field_id in self.question_text_field_ids
            if field_id not in self.named_blocks
        ]

    def output_answers(self, redact_pii=False, mark_pii=False):
        # Returns a safe string of the rendered answers
        return mark_safe(
            "".join(self.render_answers(redact_pii=redact_pii, mark_pii=mark_pii))
        )

    def output_text_answers(self):
        return mark_safe("".join(self.render_text_blocks_answers()))

    def output_first_group_text_answers(self):
        return mark_safe("".join(self.render_first_group_text_answers()))

    def get_answer_from_label(self, label):
        for field_id in self.question_text_field_ids:
            if field_id not in self.named_blocks:
                question_field = self.serialize(field_id)
                if label.lower() in question_field["question"].lower():
                    if isinstance(question_field["answer"], str):
                        answer = question_field["answer"]
                    else:
                        answer = ",".join(question_field["answer"])
                    if answer and not answer == "N":
                        return answer
        return None

    def get_text_questions_answers_as_dict(self):
        """Map each text question to its answer, never redacted.

        Goes through `serialize()`, which ignores `is_pii`, so answers marked as
        personal information are included in the clear. Its one caller is the
        submission PDF download, which is `staff_required`.
        """
        data_dict = {}
        for field_id in self.question_text_field_ids:
            if field_id not in self.named_blocks:
                question_field = self.serialize(field_id)
                if isinstance(question_field["answer"], str):
                    answer = question_field["answer"]
                else:
                    answer = ",".join(question_field["answer"])
                if answer and not answer == "None":
                    data_dict[question_field["question"]] = answer
                elif question_field["type"] == "checkbox":
                    data_dict[question_field["question"]] = False
                else:
                    data_dict[question_field["question"]] = "-"
        return data_dict
