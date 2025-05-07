from django.test import TestCase, override_settings

from hypha.apply.funds.models.utils import (
    STATUS_SUCCESS,
    SubmissionExportManager,
)
from hypha.apply.funds.tasks import generate_submission_csv
from hypha.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from hypha.apply.todo.models import Task
from hypha.apply.users.tests.factories import StaffFactory


class TestTasks(TestCase):
    def test_csv_generation(self):
        submissions = ApplicationSubmissionFactory.create_batch(5)
        req_user = StaffFactory()

        generate_submission_csv.apply(
            args=[[submission.id for submission in submissions], req_user.id]
        )

        gen_csv = SubmissionExportManager.objects.all().first()

        self.assertEqual(SubmissionExportManager.objects.all().count(), 1)

        # Should be 6 rows, 1 title row and 5 serialized applications
        self.assertEqual(len(gen_csv.export_data.strip("\r\n").split("\r\n")), 6)
        self.assertEqual(gen_csv.user, req_user)
        self.assertEqual(gen_csv.status, STATUS_SUCCESS)

    def test_csv_generation_with_existing_manager(self):
        submissions = ApplicationSubmissionFactory.create_batch(5)
        req_user = StaffFactory()

        SubmissionExportManager.objects.create(
            user=req_user, total_export=1, export_data="teeeeesst"
        )

        generate_submission_csv.apply(
            args=[[submission.id for submission in submissions], req_user.id]
        )

        gen_csv = SubmissionExportManager.objects.all().first()

        # Only one Submission Export Manager should exist for the user, deleting the previous
        self.assertEqual(SubmissionExportManager.objects.all().count(), 1)

        # Should be 6 rows, 1 title row and 5 serialized applications
        self.assertEqual(len(gen_csv.export_data.strip("\r\n").split("\r\n")), 6)
        self.assertEqual(gen_csv.user, req_user)
        self.assertEqual(gen_csv.status, STATUS_SUCCESS)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_adds_csv_download_task(self):
        submissions = ApplicationSubmissionFactory.create_batch(5)
        req_user = StaffFactory()

        generate_submission_csv.apply(
            args=[[submission.id for submission in submissions], req_user.id]
        )
        self.assertEqual(Task.objects.all().count(), 1)

    def test_doesnt_adds_csv_download_task(self):
        submissions = ApplicationSubmissionFactory.create_batch(5)
        req_user = StaffFactory()

        generate_submission_csv.apply(
            args=[[submission.id for submission in submissions], req_user.id]
        )
        self.assertEqual(Task.objects.all().count(), 0)
