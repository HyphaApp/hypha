from django.test import SimpleTestCase

from .workflow import Workflow, Stage


class TestWorkflowCreation(SimpleTestCase):
    def test_can_create_workflow(self):
        name = 'single_stage'
        workflow = Workflow(name)
        self.assertEqual(workflow.name, name)


class TestStageCreation(SimpleTestCase):
    def test_can_create_stage(self):
        name = 'the_stage'
        stage = Stage(name)
        self.assertEqual(stage.name, name)
