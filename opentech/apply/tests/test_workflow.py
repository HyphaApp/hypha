from django.test import SimpleTestCase
from django.forms import Form

from opentech.apply.workflow import Action, Phase, Stage, Workflow

from .factories import ActionFactory, PhaseFactory, StageFactory, WorkflowFactory


class TestWorkflowCreation(SimpleTestCase):
    def test_can_create_workflow(self):
        stage = StageFactory()
        class NewWorkflow(Workflow):
            name = 'single_stage'
            stage_classes = [stage]
        workflow = NewWorkflow([Form()])
        self.assertEqual(workflow.name, NewWorkflow.name)
        self.assertEqual(len(workflow.stages), 1)

    def test_returns_first_phase_if_no_arg(self):
        workflow = WorkflowFactory(num_stages=1, stages__num_phases=1)
        self.assertEqual(workflow.next(), workflow.stages[0].phases[0])

    def test_can_get_the_current_phase(self):
        workflow = WorkflowFactory(num_stages=1, stages__num_phases=2)
        phase = workflow.stages[0].phases[0]
        self.assertEqual(workflow.current(str(phase)), phase)

    def test_returns_next_stage(self):
        workflow = WorkflowFactory(num_stages=2, stages__num_phases=1)
        self.assertEqual(workflow.next_stage(workflow.stages[0]), workflow.stages[1])

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
        stage = Stage(form, name=name)
        self.assertEqual(stage.name, name)
        self.assertEqual(stage.form, form)

    def test_can_get_next_phase(self):
        stage = StageFactory.build(num_phases=2)
        self.assertEqual(stage.next(stage.phases[0]), stage.phases[1])

    def test_get_none_if_no_next_phase(self):
        stage = StageFactory.build(num_phases=1)
        self.assertEqual(stage.next(stage.phases[0]), None)


class TestPhaseCreation(SimpleTestCase):
    def test_can_create_phase(self):
        name = 'the_phase'
        phase = Phase(name)
        self.assertEqual(phase.name, name)

    def test_can_get_action_from_phase(self):
        actions = ActionFactory.create_batch(3)
        action = actions[1]
        phase = PhaseFactory(actions=actions)
        self.assertEqual(phase[action.name], action)

    def test_uses_name_if_no_public(self):
        phase = Phase('Phase Name')
        self.assertEqual(phase.public_name, phase.name)

    def test_uses_public_if_provided(self):
        public_name = 'Public Name'
        phase = Phase('Phase Name', public_name=public_name)
        self.assertEqual(phase.public_name, public_name)
        self.assertNotEqual(phase.public_name, phase.name)

    def test_uses_public_if_provided_on_class(self):
        class NewPhase(Phase):
            public_name = 'Public Name'
        phase = NewPhase('Phase Name')
        self.assertEqual(phase.public_name, NewPhase.public_name)
        self.assertNotEqual(phase.public_name, phase.name)


class TestActions(SimpleTestCase):
    def test_can_create_action(self):
        name = 'action stations'
        action = Action(name)
        self.assertEqual(action.name, name)

    def test_calling_processes_the_action(self):
        action = ActionFactory()
        with self.assertRaises(NotImplementedError):
            action.process('')
