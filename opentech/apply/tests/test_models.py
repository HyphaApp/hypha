from django.test import TestCase

from opentech.apply.models import Fund
from opentech.apply.workflow import SingleStage


class TestFundModel(TestCase):
    def test_can_access_workflow_class(self):
        fund = Fund.objects.create(name='Internet Freedom Fund')
        self.assertEqual(fund.workflow, 'single')
        self.assertEqual(fund.workflow_class, SingleStage)
