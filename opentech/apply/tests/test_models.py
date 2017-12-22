from django.test import TestCase

from opentech.apply.workflow import SingleStage

from .factories import FundPageFactory


class TestFundModel(TestCase):
    def test_can_access_workflow_class(self):
        fund = FundPageFactory(parent=None)
        self.assertEqual(fund.workflow, 'single')
        self.assertEqual(fund.workflow_class, SingleStage)
