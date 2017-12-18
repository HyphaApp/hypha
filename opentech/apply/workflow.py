from typing import Dict, Iterator, Iterable, List, Sequence, Tuple, Union

from django.forms import Form


class Workflow:
    def __init__(self, name: str, stages: Sequence['Stage']) -> None:
        self.name = name
        self.stages = stages

    def current(self, current_phase: Union[str, 'Phase']) -> Union['Phase', None]:
        if isinstance(current_phase, Phase):
            return current_phase

        if not current_phase:
            return self.first()

        stage_name, phase_name, _ = current_phase.split('__')
        for stage in self.stages:
            if stage.name == stage_name:
                return stage.current(phase_name)
        return None

    def first(self) -> 'Phase':
        return self.stages[0].next()

    def process(self, current_phase: str, action: str) -> Union['Phase', None]:
        phase = self.current(current_phase)
        new_phase = phase.process(action)
        if not new_phase:
            new_stage = self.next_stage(phase.stage)
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
        for phase in phases:
            phase.stage = self
        self.phases = phases

    def __str__(self) -> str:
        return self.name

    def current(self, phase_name: str) -> 'Phase':
        for phase in self.phases:
            if phase.name == phase_name:
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

    def __init__(self, name: str) -> None:
        self.name = name
        self.stage: Union['Stage', None] = None
        self._actions = {action.name: action for action in self.actions}
        self.occurance: int = 0

    @property
    def action_names(self) -> List[str]:
        return list(self._actions.keys())

    def __str__(self) -> str:
        return '__'.join([self.stage.name, self.name, str(self.occurance)])

    def __getitem__(self, value: str) -> 'Action':
        return self._actions[value]

    def process(self, action: str) -> Union['Phase', None]:
        return self[action]()


class Action:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self) -> Union['Phase', None]:
        return self.process()

    def process(self) -> Union['Phase', None]:
        # Use this to define the behaviour of the action
        raise NotImplementedError


# --- OTF Workflow ---

class ChangePhaseAction(Action):
    def __init__(self, phase: Union['Phase', str], *args: str, **kwargs: str) -> None:
        self.target_phase = phase
        super().__init__(*args, **kwargs)

    def process(self) -> Union['Phase', None]:
        if isinstance(self.target_phase, str):
            phase = globals()[self.target_phase]
        else:
            phase = self.target_phase
        return phase


reject_action = ChangePhaseAction('rejected', 'Reject')

accept_action = ChangePhaseAction('accepted', 'Accept')

progress_external = ChangePhaseAction('external_review', 'Progress')

progress_stage = ChangePhaseAction(None, 'Progress Stage')


class ReviewPhase(Phase):
    actions = [progress_stage, reject_action]


class ProposalReviewPhase(Phase):
    actions = [progress_external, reject_action]


class FinalReviewPhase(Phase):
    actions = [accept_action, reject_action]


concept_review = ReviewPhase('Internal Review')

proposal_review = ProposalReviewPhase('Internal Review')

external_review = FinalReviewPhase('AC Review')

rejected = Phase('Rejected')

accepted = Phase('Accepted')

concept_note = Stage('Concept', Form(), [concept_review, accepted, rejected])

proposal = Stage('Proposal', Form(), [proposal_review, external_review, accepted, rejected])

single_stage = Workflow('Single Stage', [proposal])

two_stage = Workflow('Two Stage', [concept_note, proposal])
