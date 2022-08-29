import os

from django.urls import reverse

from hypha.apply.stream_forms.files import StreamFieldFile


def generate_submission_file_path(submission_id, field_id, file_name):
    path = os.path.join('submission', str(submission_id), str(field_id))
    if file_name.startswith(path):
        return file_name

    return os.path.join(path, file_name)


class SubmissionStreamFieldFile(StreamFieldFile):

    def get_submission_id(self):
        from hypha.apply.funds.models.submissions import ApplicationRevision
        submission_id = self.instance.pk

        if isinstance(self.instance, ApplicationRevision):
            submission_id = self.instance.submission.pk
        return submission_id

    def generate_filename(self):
        return generate_submission_file_path(self.get_submission_id(), self.field.id, self.name)

    @property
    def url(self):
        return reverse(
            'apply:submissions:serve_private_media', kwargs={
                'pk': self.get_submission_id(),
                'field_id': self.field.id,
                'file_name': self.basename,
            }
        )
