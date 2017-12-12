from django.test import SimpleTestCase

from .workflow import Workflow, Stage


class TestWorkflowCreation(SimpleTestCase):
    def test_can_create_workflow(self):
        name = 'single_stage'
        stage = Stage('stage_name')
        workflow = Workflow(name, stage)
        self.assertEqual(workflow.name, name)
        self.assertCountEqual(workflow.stages, [stage])

    def test_stages_required_for_workflow(self):
        name = 'single_stage'
        with self.assertRaises(ValueError):
            Workflow(name)


class TestStageCreation(SimpleTestCase):
    def test_can_create_stage(self):
        name = 'the_stage'
        stage = Stage(name)
        self.assertEqual(stage.name, name)
