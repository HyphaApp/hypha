import copy

from typing import Dict, Iterator, Iterable, List, Sequence, Tuple, Union

from django.forms import Form
from django.utils.text import slugify


class Workflow:
    def __init__(self, name: str, stages: Sequence['Stage']) -> None:
        self.name = name
        self.stages = stages

    def current(self, current_phase: Union[str, 'Phase']) -> Union['Phase', None]:
        if isinstance(current_phase, Phase):
            return current_phase

        if not current_phase:
            return self.first()

        stage_name, phase_name, occurance = current_phase.split('__')
        for stage in self.stages:
            if stage.name == stage_name:
                return stage.current(phase_name, occurance)
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
                    return self.stages[i+1]
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


class Stage:
    def __init__(self, name: str, form: Form, phases: Sequence['Phase'],
                 current_phase: Union['Phase', None]=None) -> None:
        self.name = name
        self.form = form
        # Make the phases new instances to prevent errors with mutability
        existing_phases: set = set()
        new_phases: list = list()
        for phase in phases:
            phase.stage = self
            while str(phase) in existing_phases:
                phase.occurance += 1
            existing_phases.add(str(phase))
            new_phases.append(copy.copy(phase))
        self.phases = new_phases

    def __str__(self) -> str:
        return self.name

    def current(self, phase_name: str, occurance: str) -> 'Phase':
        for phase in self.phases:
            if phase._internal == phase_name and int(occurance) == phase.occurance:
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
                    return self.phases[i+1]
                except IndexError:
                    pass
        return None

class Phase:
    actions: Sequence['Action'] = list()
    name: str = ''

    def __init__(self, name: str='') -> None:
        if name:
            self.name = name
        self._internal = slugify(self.name)
        self.stage: Union['Stage', None] = None
        self._actions = {action.name: action for action in self.actions}
        self.occurance: int = 0

    def __eq__(self, other: object) -> bool:
        to_match = ['name', 'occurance']
        return all(getattr(self, attr) == getattr(other, attr) for attr in to_match)

    @property
    def action_names(self) -> List[str]:
        return list(self._actions.keys())

    def __str__(self) -> str:
        return '__'.join([self.stage.name, self._internal, str(self.occurance)])

    def __getitem__(self, value: str) -> 'Action':
        return self._actions[value]

    def process(self, action: str) -> Union['Phase', None]:
        return self[action].process(self)


class Action:
    def __init__(self, name: str) -> None:
        self.name = name

    def process(self, phase: 'Phase') -> Union['Phase', None]:
        # Use this to define the behaviour of the action
        raise NotImplementedError


# --- OTF Workflow ---

class ChangePhaseAction(Action):
    def __init__(self, phase: Union['Phase', str], *args: str, **kwargs: str) -> None:
        self.target_phase = phase
        super().__init__(*args, **kwargs)

    def process(self, phase: 'Phase') -> Union['Phase', None]:
        if isinstance(self.target_phase, str):
            phase = globals()[self.target_phase]
        else:
            phase = self.target_phase
        return phase


class NextPhaseAction(Action):
    def process(self, phase: 'Phase') -> Union['Phase', None]:
        return phase.stage.next(phase)


reject_action = ChangePhaseAction('rejected', 'Reject')

accept_action = ChangePhaseAction('accepted', 'Accept')

progress_stage = ChangePhaseAction(None, 'Progress Stage')

next_phase = NextPhaseAction('Progress')


class ReviewPhase(Phase):
    name = 'Internal Review'
    actions = [NextPhaseAction('Close Review')]


class DeterminationPhase(Phase):
    name = 'Under Discussion'
    actions = [accept_action, reject_action]


class DeterminationWithProgressionPhase(Phase):
    name = 'Under Discussion'
    actions = [progress_stage, reject_action]


class DeterminationWithNextPhase(Phase):
    name = 'Under Discussion'
    actions = [NextPhaseAction('Open Review'), reject_action]


review = ReviewPhase()

under_discussion = DeterminationPhase()

under_discussion_next = DeterminationWithNextPhase()

should_progress = DeterminationWithProgressionPhase()

rejected = Phase(name='Rejected')

accepted = Phase(name='Accepted')

concept_note = Stage('Concept', Form(), [under_discussion_next, review, should_progress, rejected])

proposal = Stage('Proposal', Form(), [under_discussion_next, review, under_discussion_next, ReviewPhase('AC Review'), under_discussion, accepted, rejected])

single_stage = Workflow('Single Stage', [proposal])

two_stage = Workflow('Two Stage', [concept_note, proposal])
