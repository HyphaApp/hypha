from django.test import TestCase
from rest_framework.exceptions import ErrorDetail

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.projects.tests.factories import DeliverableFactory
from hypha.apply.review.tests.factories import ReviewFactory

from ..projects.serializers import DeliverableSerializer
from ..serializers import ReviewSummarySerializer


class TestReviewSummarySerializer(TestCase):
    def test_handles_no_reviews(self):
        submission = ApplicationSubmissionFactory()
        data = ReviewSummarySerializer(submission).data
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["score"], None)
        self.assertEqual(data["recommendation"], {"value": -1, "display": None})
        self.assertEqual(data["assigned"], [])
        self.assertEqual(data["reviews"], [])

    def test_handles_negative_reviews(self):
        submission = ApplicationSubmissionFactory()
        ReviewFactory(submission=submission)
        data = ReviewSummarySerializer(submission).data
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["score"], 0)
        self.assertEqual(data["recommendation"], {"value": 0, "display": "No"})
        self.assertEqual(len(data["assigned"]), 1)
        self.assertEqual(len(data["reviews"]), 1)


class TestDeliverableSerializer(TestCase):
    def test_id_is_required(self):
        serializer = DeliverableSerializer(data={"quantity": 1})
        self.assertFalse(serializer.is_valid())
        error_message = {
            "id": [ErrorDetail(string="This field is required.", code="required")]
        }
        self.assertEqual(serializer.errors, error_message)

    def test_validate_id(self):
        serializer = DeliverableSerializer(data={"id": 1, "quantity": 1})
        self.assertFalse(serializer.is_valid())
        error_message = {
            "id": {"detail": ErrorDetail(string="Not found", code="invalid")}
        }
        self.assertEqual(serializer.errors, error_message)

        deliverable = DeliverableFactory()
        serializer = DeliverableSerializer(data={"id": deliverable.id, "quantity": 1})
        self.assertTrue(serializer.is_valid())

    def test_quantity_not_required(self):
        deliverable = DeliverableFactory()
        serializer = DeliverableSerializer(data={"id": deliverable.id})
        self.assertTrue(serializer.is_valid())
