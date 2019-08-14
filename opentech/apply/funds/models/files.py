from django.urls import reverse

from opentech.apply.stream_forms.files import StreamFieldFile


class SubmissionStreamFileField(StreamFieldFile):
    @property
    def url(self):
        try:
            name_parts = self.name.split('/')
            return reverse(
                'apply:submissions:serve_private_media', kwargs={
                    'pk': name_parts[1], 'field_id': name_parts[2],
                    'file_name': name_parts[3]
                }
            )
        except IndexError:
            pass
        return super().url
