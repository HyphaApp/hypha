from django.test import TestCase

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory

from ..models import Project


class TestProjectModel(TestCase):
    def test_create_from_submission(self):
        submission = ApplicationSubmissionFactory()

        project = Project.create_from_submission(submission)

        self.assertEquals(project.submission, submission)
        self.assertEquals(project.title, submission.title)
        self.assertEquals(project.user, submission.user)
