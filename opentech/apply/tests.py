from unittest import TestCase

from .workflow import Workflow


class TestWorkflowCreation(TestCase):
    def test_can_create_workflow(self):
        name = 'single_stage'
        workflow = Workflow(name)
        self.assertEqual(workflow.name, name)
