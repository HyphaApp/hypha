from django.utils.text import mark_safe

from opentech.apply.stream_forms.blocks import FormFieldBlock
from opentech.apply.utils.blocks import MustIncludeFieldBlock


__all__ = ['AccessFormData']


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
            response = data.pop(field_name)
            data[field_id] = response
        return data

    def field(self, id):
        try:
            return self.fields[id]
        except KeyError as e:
            try:
                actual_id = self.must_include[id]
            except KeyError:
                raise e
            else:
                return self.fields[actual_id]

    def data(self, id):
        try:
            return self.form_data[id]
        except KeyError as e:
            try:
                transposed_must_include = {v: k for k, v in self.must_include.items()}
                actual_id = transposed_must_include[id]
            except KeyError:
                # We have most likely progressed application forms so the data isnt in form_data
                return None
            else:
                return self.form_data[actual_id]

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
