from django.test import SimpleTestCase
from django.forms import Form

from opentech.apply.workflow import Stage, Workflow

from .factories import StageFactory, WorkflowFactory


class TestWorkflowCreation(SimpleTestCase):
    def test_can_create_workflow(self):
        name = 'single_stage'
        stage = StageFactory()
        workflow = Workflow(name, [stage])
        self.assertEqual(workflow.name, name)
        self.assertCountEqual(workflow.stages, [stage])

    def test_can_iterate_through_workflow(self):
        stages = StageFactory.create_batch(2)
        workflow = Workflow('two_stage', stages)
        for stage, check in zip(workflow, stages):
            self.assertEqual(stage, check)

    def test_returns_first_stage_if_no_arg(self):
        workflow = WorkflowFactory(num_stages=1)
        self.assertEqual(workflow.next(), workflow.stages[0])

    def test_returns_none_if_no_next(self):
        workflow = WorkflowFactory(num_stages=1)
        self.assertEqual(workflow.next(workflow.stages[0]), None)

    def test_returns_next_stage(self):
        workflow = WorkflowFactory(num_stages=2)
        self.assertEqual(workflow.next(workflow.stages[0]), workflow.stages[1])


class TestStageCreation(SimpleTestCase):
    def test_can_create_stage(self):
        name = 'the_stage'
        form = Form()
        stage = Stage(name, form)
        self.assertEqual(stage.name, name)
        self.assertEqual(stage.form, form)
