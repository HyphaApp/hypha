from operator import attrgetter

from django.test import TestCase

from opentech.apply.funds.models import RoundsAndLabs

from opentech.apply.funds.tests.factories import (
    ApplicationSubmissionFactory,
    FundTypeFactory,
    LabFactory,
    LabSubmissionFactory,
    RoundFactory,
)


class BaseRoundsAndLabTestCase:
    def test_can_get(self):
        obj = self.base_factory()
        qs = RoundsAndLabs.objects.all()
        self.assertEqual(qs.first(), obj)

    def test_with_progress(self):
        obj = self.base_factory()
        self.submission_factory(**{self.relation_to_app: obj})
        qs = RoundsAndLabs.objects.with_progress()
        fetched_obj = qs.first()
        self.assertEqual(fetched_obj.total_submissions, 1)
        self.assertEqual(fetched_obj.closed_submissions, 0)
        self.assertEqual(fetched_obj.progress, 0)

    def test_with_determined(self):
        obj = self.base_factory()
        self.submission_factory(**{self.relation_to_app: obj}, rejected=True)
        qs = RoundsAndLabs.objects.with_progress()
        fetched_obj = qs.first()
        self.assertEqual(fetched_obj.total_submissions, 1)
        self.assertEqual(fetched_obj.closed_submissions, 1)
        self.assertEqual(fetched_obj.progress, 100)

    def test_annotated(self):
        obj = self.base_factory()
        qs = RoundsAndLabs.objects.with_progress()
        fetched_obj = qs.first()
        self.assertEqual(fetched_obj.lead, obj.lead.full_name)
        self.assertEqual(fetched_obj.start_date, getattr(obj, 'start_date', None))
        self.assertEqual(fetched_obj.end_date, getattr(obj, 'end_date', None))
        self.assertEqual(fetched_obj.parent_path, obj.get_parent().path)
        self.assertEqual(fetched_obj.fund, getattr(getattr(obj, 'fund', None), 'title', None))

    def test_active(self):
        obj = self.base_factory()
        self.submission_factory(**{self.relation_to_app: obj})
        base_qs = RoundsAndLabs.objects.with_progress()
        fetched_obj = base_qs.active().first()
        self.assertEqual(fetched_obj, obj)
        self.assertFalse(base_qs.inactive().exists())

    def test_no_submissions_not_either(self):
        self.base_factory()
        base_qs = RoundsAndLabs.objects.with_progress()
        self.assertFalse(base_qs.inactive().exists())
        self.assertFalse(base_qs.active().exists())

    def test_inactive(self):
        obj = self.base_factory()
        self.submission_factory(**{self.relation_to_app: obj}, rejected=True)
        base_qs = RoundsAndLabs.objects.with_progress()
        fetched_obj = base_qs.inactive().first()
        self.assertEqual(fetched_obj, obj)
        self.assertFalse(base_qs.active().exists())


class TestForLab(BaseRoundsAndLabTestCase, TestCase):
    base_factory = LabFactory
    submission_factory = LabSubmissionFactory
    relation_to_app = 'page'

    # Specific tests as labs and round have very different behaviour here
    def test_new(self):
        self.base_factory()
        fetched_obj = RoundsAndLabs.objects.new().first()
        self.assertIsNone(fetched_obj)

    def test_closed(self):
        self.base_factory()
        fetched_obj = RoundsAndLabs.objects.closed().first()
        self.assertIsNone(fetched_obj)

    def test_open(self):
        obj = self.base_factory()
        fetched_obj = RoundsAndLabs.objects.open().first()
        self.assertEqual(fetched_obj, obj)


class TestForRound(BaseRoundsAndLabTestCase, TestCase):
    base_factory = RoundFactory
    submission_factory = ApplicationSubmissionFactory
    relation_to_app = 'round'

    # Specific tests as labs and round have very different behaviour here
    def test_new(self):
        round = self.base_factory()
        fetched_obj = RoundsAndLabs.objects.new().first()
        self.assertEqual(fetched_obj, round)

    def test_closed(self):
        round = self.base_factory(closed=True)
        fetched_obj = RoundsAndLabs.objects.closed().first()
        self.assertEqual(fetched_obj, round)

    def test_open(self):
        obj = self.base_factory(now=True)
        fetched_obj = RoundsAndLabs.objects.open().first()
        self.assertEqual(fetched_obj, obj)


class TestRoundsAndLabsManager(TestCase):
    def test_cant_get_fund(self):
        FundTypeFactory()
        qs = RoundsAndLabs.objects.all()
        self.assertEqual(qs.count(), 0)

    def test_doesnt_confuse_lab_and_round(self):
        round = RoundFactory()
        lab = LabFactory()

        # Lab 50% progress
        LabSubmissionFactory(page=lab)
        LabSubmissionFactory(page=lab, rejected=True)

        # Round 0% progress
        ApplicationSubmissionFactory.create_batch(2, round=round)

        fetched_lab = RoundsAndLabs.objects.with_progress().last()
        fetched_round = RoundsAndLabs.objects.with_progress().first()

        self.assertEqual([fetched_round, fetched_lab], [round, lab])

        self.assertEqual(fetched_round.progress, 0)
        self.assertEqual(fetched_lab.progress, 50)
