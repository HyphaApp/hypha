from django.test import TestCase

from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.projects.tests.factories import (
    PaymentRequestFactory,
    ProjectFactory,
    ReportFactory,
)

from ..models import Activity
from .factories import ActivityFactory, CommentFactory


class TestActivityOnlyIncludesCurrent(TestCase):
    def test_doesnt_include_non_current(self):
        CommentFactory()
        CommentFactory(current=False)
        self.assertEqual(Activity.comments.count(), 1)


class TestActivityModel(TestCase):
    def test_can_save_source_application(self):
        other = ApplicationSubmissionFactory()
        activity = ActivityFactory(source=other)
        self.assertEqual(other, activity.source)
        self.assertTrue(str(activity))

    def test_can_save_source_project(self):
        other = ProjectFactory()
        activity = ActivityFactory(source=other)
        self.assertEqual(other, activity.source)
        self.assertTrue(str(activity))

    def test_can_save_related_paymentRequest(self):
        other = PaymentRequestFactory()
        activity = ActivityFactory(related_object=other)
        self.assertEqual(other, activity.related_object)

    def test_can_save_related_report(self):
        other = ReportFactory()
        activity = ActivityFactory(related_object=other)
        self.assertEqual(other, activity.related_object)
