from collections import defaultdict
import copy
import itertools

from typing import Dict, Iterable, Iterator, List, Sequence, Type, Union

from django.forms import Form
from django.utils.text import slugify

"""
This file defines classes which allow you to compose workflows based on the following structure:

Workflow -> Stage -> Phase -> Action

These classes are designed such that they can be mapped to a wagtail streamfield to allow admins
to build/adjust workflows as required.

Current limitations:
* Changing the name of a phase will mean that any object which references it cannot progress. [will
be fixed when streamfield, may require intermediate fix prior to launch]
* Outcomes are a special case of phase and perhaps should be handled separately. [will look at when
progressing stages]
"""


def phase_name(stage: 'Stage', phase: Union['Phase', str], step: int) -> str:
    # Build the identifiable name for a phase
    if not isinstance(phase, str):
        phase_name = phase._internal
    else:
        phase_name = phase

    return '__'.join([stage.name, phase_name, str(step)])


class Workflow(Iterable):
    """
    A Workflow is a collection of Stages an application goes through. When a Stage is complete,
    it will return the next Stage in the list or `None` if no such Stage exists.
    """
    name: str = ''
    stage_classes: Sequence[Type['Stage']] = list()

    def __init__(self, forms: Sequence[Form]) -> None:
        if len(self.stage_classes) != len(forms):
            raise ValueError('Number of forms does not equal the number of stages')

        self.stages = [stage(form) for stage, form in zip(self.stage_classes, forms)]

    def __iter__(self) -> Iterator['Phase']:
        for stage in self.stages:
            yield from stage

    def current(self, current_phase: Union[str, 'Phase']) -> Union['Phase', None]:
        if isinstance(current_phase, Phase):
            return current_phase

        if not current_phase:
            return self.first()

        for stage in self.stages:
            phase = stage.get_phase(current_phase)
            if phase:
                return phase

        return None

    def first(self) -> 'Phase':
        return self.stages[0].next()

    def process(self, current_phase: str, action: str) -> Union['Phase', None]:
        phase = self.current(current_phase)
        new_phase = phase.process(action)
        if not new_phase:
            new_stage = self.next_stage(phase.stage)
            if new_stage:
                return new_stage.first()
        return new_phase

    def next_stage(self, current_stage: 'Stage') -> 'Stage':
        for i, stage in enumerate(self.stages):
            if stage == current_stage:
                try:
                    return self.stages[i + 1]
                except IndexError:
                    pass

        return None

    def next(self, current_phase: Union[str, 'Phase']=None) -> Union['Phase', None]:
        if not current_phase:
            return self.first()

        phase = self.current(current_phase)

        for stage in self.stages:
            if stage == phase.stage:
                next_phase = stage.next(phase)
                if not next_phase:
                    continue
                return next_phase

        next_stage = self.next_stage(phase.stage)
        if next_stage:
            return stage.next()
        return None

    def __str__(self) -> str:
        return self.name


class Stage(Iterable):
    """
    Holds the Phases that are progressed through as part of the workflow process
    """
    name: str = 'Stage'
    phases: list = list()

    def __init__(self, form: Form, name: str='') -> None:
        if name:
            self.name = name
        # For OTF each stage is associated with a form submission
        # So each time they start a stage they should submit new information
        # TODO: consider removing form from stage as the stage is generic and
        # shouldn't care about forms.
        self.form = form
        self.steps = len(self.phases)
        # Make the phases new instances to prevent errors with mutability
        self.phases = self.copy_phases(self.phases)

    def copy_phases(self, phases: List['Phase']) -> List['Phase']:
        new_phases = list()
        for step, phase in enumerate(self.phases):
            try:
                new_phases.append(self.copy_phase(phase, step))
            except AttributeError:
                # We have a step with multiple equivalent phases
                for sub_phase in phase:
                    new_phases.append(self.copy_phase(sub_phase, step))
        return new_phases

    def copy_phase(self, phase: 'Phase', step: int) -> 'Phase':
        phase.stage = self
        phase.step = step
        return copy.copy(phase)

    def __iter__(self) -> 'PhaseIterator':
        return PhaseIterator(self.phases, self.steps)

    def __str__(self) -> str:
        return self.name

    def get_phase(self, phase_name: str) -> 'Phase':
        for phase in self.phases:
            if phase == phase_name:
                return phase

        # We don't have the exact name
        for phase in self.phases:
            if phase._internal == phase_name:
                # Grab the first phase to match the name
                return phase

        return None

    def first(self) -> 'Phase':
        return self.phases[0]

    def next(self, current_phase: 'Phase'=None) -> 'Phase':
        if not current_phase:
            return self.first()

        for i, phase in enumerate(self.phases):
            if phase == current_phase:
                try:
                    return self.phases[i + 1]
                except IndexError:
                    pass
        return None


class PhaseIterator(Iterator):
    class Step:
        """Allow handling phases which are equivalent e.g. outcomes (accepted/rejected)
        Delegates to the underlying phases except where naming is concerned
        """
        def __init__(self, phases: List['Phase']) -> None:
            self.phases = phases

        @property
        def step(self) -> int:
            return self.phases[0].step

        @property
        def name(self) -> str:
            # Hardcode a name for multi-phased step - always outcome at the moment
            if len(self.phases) > 1:
                return 'Outcome'
            return self.phases[0].name

        def __eq__(self, other: object) -> bool:
            return any(phase == other for phase in self.phases)

    def __init__(self, phases: List['Phase'], steps: int) -> None:
        self.current = 0
        self.phases: Dict[int, List['Phase']] = defaultdict(list)
        for phase in phases:
            self.phases[phase.step].append(phase)
        self.steps = steps

    def __iter__(self) -> 'PhaseIterator':
        return self

    def __next__(self) -> 'Step':
        self.current += 1
        if self.current > self.steps:
            raise StopIteration
        return self.Step(self.phases[self.current - 1])


class Phase:
    """
    Holds the Actions which a user can perform at each stage. A Phase with no actions is
    essentially locked
    """
    actions: Sequence['Action'] = list()
    name: str = ''
    public_name: str = ''

    def __init__(self, name: str='', public_name: str ='', active: bool=True) -> None:
        if name:
            self.name = name

        self.active = active

        if public_name:
            self.public_name = public_name
        elif not self.public_name:
            self.public_name = self.name

        self._internal = slugify(self.name)
        self.stage: Union['Stage', None] = None
        self._actions = {action.name: action for action in self.actions}
        self.step: int = 0

    def __eq__(self, other: Union[object, str]) -> bool:
        if isinstance(other, str):
            return str(self) == other
        to_match = ['name', 'step']
        return all(getattr(self, attr) == getattr(other, attr) for attr in to_match)

    @property
    def action_names(self) -> List[str]:
        return list(self._actions.keys())

    def __str__(self) -> str:
        return phase_name(self.stage, self, self.step)

    def __getitem__(self, value: str) -> 'Action':
        return self._actions[value]

    def process(self, action: str) -> Union['Phase', None]:
        return self[action].process(self)


class Action:
    """
    Base Action class.

    Actions return the Phase within the current Stage which the workflow should progress to next.
    A value of `None` will allow the Stage to progress.
    """
    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, phase: 'Phase') -> Union['Phase', None]:
        # Use this to define the behaviour of the action
        raise NotImplementedError


class ChangePhaseAction(Action):
    # Change to a specific Phase
    def __init__(self, phase: Union['Phase', str], *args: str, **kwargs: str) -> None:
        self.target_phase = phase
        super().__init__(*args, **kwargs)

    def process(self, phase: 'Phase') -> Union['Phase', None]:
        if isinstance(self.target_phase, str):
            return phase.stage.get_phase(self.target_phase)
        return self.target_phase


class NextPhaseAction(Action):
    # Change to the next action in the current Stage
    def process(self, phase: 'Phase') -> Union['Phase', None]:
        return phase.stage.next(phase)


# --- OTF Workflow ---


reject_action = ChangePhaseAction('rejected', 'Reject')

accept_action = ChangePhaseAction('accepted', 'Accept')

progress_stage = ChangePhaseAction(None, 'Invite to Proposal')

next_phase = NextPhaseAction('Progress')


class ReviewPhase(Phase):
    name = 'Internal Review'
    public_name = 'In review'
    actions = [NextPhaseAction('Close Review')]


class DiscussionWithProgressionPhase(Phase):
    name = 'Under Discussion'
    public_name = 'In review'
    actions = [progress_stage, reject_action]


class DiscussionPhase(Phase):
    name = 'Under Discussion'
    public_name = 'In review'
    actions = [accept_action, reject_action]


class DiscussionWithNextPhase(Phase):
    name = 'Under Discussion'
    public_name = 'In review'
    actions = [NextPhaseAction('Open Review'), reject_action]


rejected = Phase(name='Rejected', active=False)

accepted = Phase(name='Accepted', active=False)


class RequestStage(Stage):
    name = 'Request'
    phases = [
        DiscussionWithNextPhase(),
        ReviewPhase(),
        DiscussionPhase(),
        [accepted, rejected]
    ]


class ConceptStage(Stage):
    name = 'Concept'
    phases = [
        DiscussionWithNextPhase(),
        ReviewPhase(),
        [DiscussionWithProgressionPhase(), rejected]
    ]


class ProposalStage(Stage):
    name = 'Proposal'
    phases = [
        DiscussionWithNextPhase(),
        ReviewPhase(),
        DiscussionWithNextPhase(),
        ReviewPhase('AC Review', public_name='In AC review'),
        DiscussionPhase(public_name='In AC review'),
        [accepted, rejected]
    ]


class SingleStage(Workflow):
    name = 'Single Stage'
    stage_classes = [RequestStage]


class DoubleStage(Workflow):
    name = 'Two Stage'
    stage_classes = [ConceptStage, ProposalStage]


statuses = set(phase.name for phase in Phase.__subclasses__())
status_options = [(slugify(opt), opt) for opt in statuses]


def get_active_statuses():
    active = set()

    def add_if_active(phase):
        if phase.active:
            active.add(str(phase))

    for phase in itertools.chain(SingleStage([None]), DoubleStage([None, None])):
        try:
            add_if_active(phase)
        except AttributeError:
            # it is actually a step
            step = phase
            for phase in step.phases:
                add_if_active(phase)
    return active


active_statuses = get_active_statuses()
