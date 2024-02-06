from django.test import override_settings
from django.urls import reverse_lazy
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from hypha.apply.funds.models import ScreeningStatus
from hypha.apply.funds.tests.factories.models import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import ReviewerFactory, StaffFactory, UserFactory


@override_settings(SECURE_SSL_REDIRECT=False)
class ScreeningStatusViewSetTests(APITestCase):
    def setUp(self):
        ScreeningStatus.objects.all().delete()
        self.yes_screening_status = baker.make("funds.ScreeningStatus", yes=True)

    def get_screening_status_url(self, pk=None):
        if pk:
            return reverse_lazy("api:v1:screenings-detail", kwargs={"pk": pk})
        return reverse_lazy("api:v1:screenings-list")

    def test_staff_can_list_screening_statuses(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.get_screening_status_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), ScreeningStatus.objects.count())
        self.assertEqual(response.json()[0]["id"], self.yes_screening_status.id)
        self.assertEqual(response.json()[0]["title"], self.yes_screening_status.title)
        self.assertEqual(response.json()[0]["yes"], self.yes_screening_status.yes)
        self.assertEqual(
            response.json()[0]["default"], self.yes_screening_status.default
        )

    def test_staff_can_view_screening_statuses_detail(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        response = self.client.get(
            self.get_screening_status_url(pk=self.yes_screening_status.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_cant_list_screening_statuses(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.get_screening_status_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reviewer_cant_list_screening_statuses(self):
        user = ReviewerFactory()
        self.client.force_authenticate(user)
        response = self.client.get(self.get_screening_status_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(SECURE_SSL_REDIRECT=False)
class SubmissionScreeningStatusViewSetTests(APITestCase):
    def setUp(self):
        ScreeningStatus.objects.all().delete()
        self.yes_screening_status = baker.make("funds.ScreeningStatus", yes=True)
        self.yes_default_screening_status = baker.make(
            "funds.ScreeningStatus", yes=True, default=True
        )
        self.no_screening_status = baker.make("funds.ScreeningStatus", yes=False)
        self.no_default_screening_status = baker.make(
            "funds.ScreeningStatus", yes=False, default=True
        )
        self.submission = ApplicationSubmissionFactory()

    def get_submission_screening_status_url(self, submission_id=None):
        return reverse_lazy(
            "api:v1:submission-screening_statuses-list",
            kwargs={"submission_pk": submission_id},
        )

    def test_cant_add_screening_status_without_setting_default(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.clear()
        response = self.client.post(
            self.get_submission_screening_status_url(submission_id=self.submission.id),
            data={"id": self.yes_screening_status.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"],
            "Can't set screening decision without default being set",
        )

    def test_cant_add_two_types_of_screening_status(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.clear()
        self.submission.screening_statuses.add(self.yes_default_screening_status)
        response = self.client.post(
            self.get_submission_screening_status_url(submission_id=self.submission.id),
            data={"id": self.no_screening_status.id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"],
            "Can't set screening decision for both yes and no",
        )

    def test_add_screening_status(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.clear()
        self.submission.screening_statuses.add(self.yes_default_screening_status)
        response = self.client.post(
            self.get_submission_screening_status_url(submission_id=self.submission.id),
            data={"id": self.yes_screening_status.id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.json()), 2)

        possible_ids = [
            self.yes_screening_status.id,
            self.yes_default_screening_status.id,
        ]
        self.assertIn(response.json()[0]["id"], possible_ids)
        self.assertIn(response.json()[1]["id"], possible_ids)

    def test_staff_can_list_submission_screening_statuses(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.clear()
        response = self.client.get(
            self.get_submission_screening_status_url(submission_id=self.submission.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 0)

    def test_set_default_screening_status(self):
        user = StaffFactory()
        self.submission.screening_statuses.clear()
        self.client.force_authenticate(user)
        response = self.client.post(
            reverse_lazy(
                "api:v1:submission-screening_statuses-default",
                kwargs={"submission_pk": self.submission.id},
            ),
            data={"yes": True},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        default_set = self.submission.screening_statuses.get(default=True)
        self.assertEqual(response.json()["id"], default_set.id)
        self.assertEqual(response.json()["yes"], default_set.yes)

    def test_change_default_screening_status(self):
        user = StaffFactory()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.clear()
        response = self.client.post(
            reverse_lazy(
                "api:v1:submission-screening_statuses-default",
                kwargs={"submission_pk": self.submission.id},
            ),
            data={"yes": True},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        default_set = self.submission.screening_statuses.get(default=True)
        self.assertEqual(response.json()["id"], default_set.id)
        self.assertEqual(response.json()["yes"], default_set.yes)

        response = self.client.post(
            reverse_lazy(
                "api:v1:submission-screening_statuses-default",
                kwargs={"submission_pk": self.submission.id},
            ),
            data={"yes": False},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        default_set = self.submission.screening_statuses.get(default=True)
        self.assertEqual(response.json()["id"], default_set.id)
        self.assertEqual(response.json()["yes"], default_set.yes)

    def test_cant_change_default_screening_status(self):
        user = StaffFactory()
        self.submission.screening_statuses.clear()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.add(
            self.yes_default_screening_status, self.yes_screening_status
        )
        response = self.client.post(
            reverse_lazy(
                "api:v1:submission-screening_statuses-default",
                kwargs={"submission_pk": self.submission.id},
            ),
            data={"yes": False},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        default_set = self.submission.screening_statuses.get(default=True)
        self.assertEqual(response.json()["id"], default_set.id)
        self.assertEqual(response.json()["yes"], default_set.yes)

    def test_remove_submission_screening_status(self):
        user = StaffFactory()
        self.submission.screening_statuses.clear()
        self.client.force_authenticate(user)
        self.submission.screening_statuses.add(
            self.yes_default_screening_status, self.yes_screening_status
        )
        response = self.client.delete(
            reverse_lazy(
                "api:v1:submission-screening_statuses-detail",
                kwargs={
                    "submission_pk": self.submission.id,
                    "pk": self.yes_screening_status.id,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)

    def test_cant_remove_submission_default_screening_status(self):
        user = StaffFactory()
        self.submission.screening_statuses.clear()
        self.submission.screening_statuses.add(self.yes_default_screening_status)
        self.client.force_authenticate(user)
        response = self.client.delete(
            reverse_lazy(
                "api:v1:submission-screening_statuses-detail",
                kwargs={
                    "submission_pk": self.submission.id,
                    "pk": self.yes_default_screening_status.id,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["detail"], "Can't delete default screening decision."
        )

    def test_cant_remove_not_set_screening_status(self):
        user = StaffFactory()
        self.submission.screening_statuses.clear()
        self.client.force_authenticate(user)
        response = self.client.delete(
            reverse_lazy(
                "api:v1:submission-screening_statuses-detail",
                kwargs={
                    "submission_pk": self.submission.id,
                    "pk": self.yes_screening_status.id,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cant_list_screening_statuses(self):
        user = UserFactory()
        self.client.force_authenticate(user)
        response = self.client.get(
            self.get_submission_screening_status_url(submission_id=self.submission.id)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reviewer_cant_list_screening_statuses(self):
        user = ReviewerFactory()
        self.client.force_authenticate(user)
        response = self.client.get(
            self.get_submission_screening_status_url(submission_id=self.submission.id)
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
