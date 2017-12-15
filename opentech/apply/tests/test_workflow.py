import itertools
from django.test import SimpleTestCase
from django.forms import Form

from opentech.apply.workflow import Phase, Stage, Workflow

from .factories import PhaseFactory, StageFactory, WorkflowFactory


class TestWorkflowCreation(SimpleTestCase):
    def test_can_create_workflow(self):
        name = 'single_stage'
        stage = StageFactory()
        workflow = Workflow(name, [stage])
        self.assertEqual(workflow.name, name)
        self.assertCountEqual(workflow.stages, [stage])

    def test_returns_first_phase_if_no_arg(self):
        workflow = WorkflowFactory(num_stages=1, stages__num_phases=1)
        self.assertEqual(workflow.next(), workflow.stages[0].phases[0])

    def test_returns_none_if_no_next(self):
        workflow = WorkflowFactory(num_stages=1, stages__num_phases=1)
        self.assertEqual(workflow.next(workflow.stages[0].phases[0]), None)

    def test_returns_next_phase(self):
        workflow = WorkflowFactory(num_stages=2, stages__num_phases=1)
        self.assertEqual(workflow.next(workflow.stages[0].phases[0]), workflow.stages[1].phases[0])

    def test_returns_next_phase_shared_name(self):
        workflow = WorkflowFactory(num_stages=1, stages__num_phases=3, stages__phases__name='the_same')
        self.assertEqual(workflow.next(workflow.stages[0].phases[0]), workflow.stages[0].phases[1])


class TestStageCreation(SimpleTestCase):
    def test_can_create_stage(self):
        name = 'the_stage'
        form = Form()
        phases = PhaseFactory.create_batch(2)
        stage = Stage(name, form, phases)
        self.assertEqual(stage.name, name)
        self.assertEqual(stage.form, form)
        self.assertEqual(stage.phases, phases)

    def test_can_iterate_through_phases(self):
        stage = StageFactory()
        for phase, check in zip(stage, stage.phases):  # type: ignore # spurious error
            self.assertEqual(phase, check)


class TestPhaseCreation(SimpleTestCase):
    def test_can_create_phase(self):
        name = 'the_phase'
        phase = Phase(name)
        self.assertEqual(phase.name, name)
