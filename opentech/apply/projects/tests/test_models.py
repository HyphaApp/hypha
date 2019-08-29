from django.test import TestCase

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory

from ..models import Project
from .factories import (DocumentCategoryFactory, PacketFileFactory,
                        ProjectFactory)


class TestProjectModel(TestCase):
    def test_create_from_submission(self):
        submission = ApplicationSubmissionFactory()

        project = Project.create_from_submission(submission)

        self.assertEquals(project.submission, submission)
        self.assertEquals(project.title, submission.title)
        self.assertEquals(project.user, submission.user)

    def test_get_missing_document_categories_with_enough_documents(self):
        project = ProjectFactory()
        category = DocumentCategoryFactory(recommended_minimum=1)
        PacketFileFactory(project=project, category=category)

        self.assertEqual(project.packet_files.count(), 1)

        missing = list(project.get_missing_document_categories())

        self.assertEqual(len(missing), 0)

    def test_get_missing_document_categories_with_no_documents(self):
        project = ProjectFactory()
        category = DocumentCategoryFactory(recommended_minimum=1)

        self.assertEqual(project.packet_files.count(), 0)

        missing = list(project.get_missing_document_categories())

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['category'], category)
        self.assertEqual(missing[0]['difference'], 1)

    def test_get_missing_document_categories_with_some_documents(self):
        project = ProjectFactory()

        category1 = DocumentCategoryFactory(recommended_minimum=5)
        PacketFileFactory(project=project, category=category1)
        PacketFileFactory(project=project, category=category1)

        category2 = DocumentCategoryFactory(recommended_minimum=3)
        PacketFileFactory(project=project, category=category2)

        self.assertEqual(project.packet_files.count(), 3)

        missing = list(project.get_missing_document_categories())

        self.assertEqual(len(missing), 2)
        self.assertEqual(missing[0]['category'], category1)
        self.assertEqual(missing[0]['difference'], 3)
        self.assertEqual(missing[1]['category'], category2)
        self.assertEqual(missing[1]['difference'], 2)
