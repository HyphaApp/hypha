import copy

from typing import List, Sequence, Type, Union

from django.forms import Form
from django.utils.text import slugify


class Workflow:
    name: str = ''
    stage_classes: Sequence[Type['Stage']] = list()

    def __init__(self, forms: Sequence[Form]) -> None:
        if len(self.stage_classes) != len(forms):
            raise ValueError('Number of forms does not equal the number of stages')

        self.stages = [stage(form) for stage, form in zip(self.stage_classes, forms)]

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
    name: str = 'Stage'
    phases: list = list()

    def __init__(self, form: Form, name: str='') -> None:
        if name:
            self.name = name
        self.form = form
        # Make the phases new instances to prevent errors with mutability
        existing_phases: set = set()
        new_phases: list = list()
        for phase in self.phases:
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
    public_name: str = ''

    def __init__(self, name: str='', public_name:str = '') -> None:
        if name:
            self.name = name

        if public_name:
            self.public_name = public_name
        elif not self.public_name:
            self.public_name = self.name

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
            return phase.stage.current(self.target_phase, '0')
        return self.target_phase


class NextPhaseAction(Action):
    def process(self, phase: 'Phase') -> Union['Phase', None]:
        return phase.stage.next(phase)


reject_action = ChangePhaseAction('rejected', 'Reject')

accept_action = ChangePhaseAction('accepted', 'Accept')

progress_stage = ChangePhaseAction(None, 'Invite to Proposal')

next_phase = NextPhaseAction('Progress')


class ReviewPhase(Phase):
    name = 'Internal Review'
    public_name = 'In review'
    actions = [NextPhaseAction('Close Review')]


class DeterminationWithProgressionPhase(Phase):
    name = 'Under Discussion'
    public_name = 'In review'
    actions = [progress_stage, reject_action]


class DeterminationPhase(Phase):
    name = 'Under Discussion'
    public_name = 'In review'
    actions = [accept_action, reject_action]


class DeterminationWithNextPhase(Phase):
    name = 'Under Discussion'
    public_name = 'In review'
    actions = [NextPhaseAction('Open Review'), reject_action]


rejected = Phase(name='Rejected')

accepted = Phase(name='Accepted')


class ConceptStage(Stage):
    name = 'Concept'
    phases = [
        DeterminationWithNextPhase(),
        ReviewPhase(),
        DeterminationWithProgressionPhase(),
        rejected,
    ]


class ProposalStage(Stage):
    name = 'Proposal'
    phases = [
        DeterminationWithNextPhase(),
        ReviewPhase(),
        DeterminationWithNextPhase(),
        ReviewPhase('AC Review', public_name='In AC review'),
        DeterminationPhase(public_name='In AC review'),
        accepted,
        rejected,
    ]


class SingleStage(Workflow):
    name = 'Single Stage'
    stage_classes = [ConceptStage]


class DoubleStage(Workflow):
    name = 'Two Stage'
    stage_classes = [ConceptStage, ProposalStage]
