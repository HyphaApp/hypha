from django.test import TestCase

from hypha.apply.funds.models import ApplicationRevision, ApplicationSubmission
from hypha.apply.funds.signals import revision_files_to_delete

from .factories import ApplicationRevisionFactory, ApplicationSubmissionFactory


class TestRevisionFilesToDelete(TestCase):
    def setUp(self):
        submission = ApplicationSubmissionFactory(with_files=True)
        self.submission = ApplicationSubmission.objects.get(id=submission.id)
        self.field_id = next(
            field_id
            for field_id in self.submission.file_field_ids
            if isinstance(self.submission.data(field_id), list)
        )
        self.kept, self.removed = self.submission.data(self.field_id)

    def form_data(self, files):
        form_data = dict(self.submission.live_revision.form_data)
        for field_id in self.submission.file_field_ids:
            form_data[field_id] = []
        form_data[self.field_id] = [
            {"name": f.name, "filename": f.filename} for f in files
        ]
        return form_data

    def make_revision(self, files):
        revision = ApplicationRevisionFactory(
            submission=self.submission, form_data=self.form_data(files)
        )
        return ApplicationRevision.objects.get(pk=revision.pk)

    def test_files_in_use_are_kept(self):
        revision = self.make_revision([self.kept, self.removed])
        self.assertEqual(revision_files_to_delete(revision), [])

    def test_files_not_in_use_are_deleted(self):
        revision = self.make_revision([self.kept, self.removed])
        # Only this revision still uses the removed file.
        form_data = self.form_data([self.kept])
        ApplicationSubmission.objects.filter(pk=self.submission.pk).update(
            form_data=form_data
        )
        self.submission.revisions.exclude(pk=revision.pk).update(form_data=form_data)
        revision = ApplicationRevision.objects.get(pk=revision.pk)

        names = [f.name for f in revision_files_to_delete(revision)]
        self.assertEqual(names, [self.removed.name])
