from django.test import TestCase

from opentech.apply.workflow import SingleStage

from .factories import FundTypeFactory


class TestFundModel(TestCase):
    def test_can_access_workflow_class(self):
        fund = FundTypeFactory(parent=None)
        self.assertEqual(fund.workflow, 'single')
        self.assertEqual(fund.workflow_class, SingleStage)
