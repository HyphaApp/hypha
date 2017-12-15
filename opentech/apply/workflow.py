from typing import Dict, Iterator, Iterable, Sequence, Tuple, Union

from django.forms import Form


class Workflow:
    def __init__(self, name: str, stages: Sequence['Stage']) -> None:
        self.name = name
        self.stages = stages
        self.mapping = self.build_mapping(stages)

    def build_mapping(self, stages: Sequence['Stage']) -> Dict[str, Tuple[int, int]]:
        mapping: Dict[str, Tuple[int, int]] = {}
        for i, stage in enumerate(stages):
            for j, phase in enumerate(stage):
                while str(phase) in mapping:
                    phase.occurance += 1
                mapping[str(phase)] = (i, j)
        return mapping

    def current_index(self, phase: Union['Phase', str, None]):
        if isinstance(phase, Phase):
            phase = str(phase)
        try:
            return self.mapping[phase]
        except KeyError:
            return 0, -1

    def __getitem__(self, value):
        return self.stages[value[0]].phases[value[1]]

    def current(self, current_phase: str):
        return self[self.current_index(current_phase)]

    def next(self, current_phase: Union['Phase', str]=None) -> Union['Phase', None]:
        stage_idx, phase_idx = self.current_index(current_phase)
        try:
            return self[stage_idx, phase_idx + 1]
        except IndexError:
            try:
                return self[stage_idx + 1, 0]
            except IndexError:
                return None


class Stage(Iterable['Phase']):
    def __init__(self, name: str, form: Form, phases: Sequence['Phase'],
                 current_phase: Union['Phase', None]=None) -> None:
        self.name = name
        self.form = form
        for phase in phases:
            phase.stage = self
        self.phases = phases

    def __iter__(self) -> Iterator['Phase']:
        yield from self.phases

    def __str__(self):
        return self.name


class Phase:
    def __init__(self, name: str, actions: Sequence['Action']) -> None:
        self.name = name
        self.stage: Union['Stage', None] = None
        self._actions= {action.name: action for action in actions}
        self.occurance: int = 0

    @property
    def actions(self):
        return list(self._actions.keys())

    def __str__(self):
        return '__'.join([self.stage.name, self.name, str(self.occurance)])

    def __getitem__(self, value):
        return self._actions[value]


class Action:
    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.process(*args, **kwargs)

    def process(self, *args, **kwargs):
        # Use this to define the behaviour of the action
        raise NotImplementedError


# --- OTF Workflow ---

class ReviewPhase(Phase):
    pass


next_phase = Action('next')

internal_review = ReviewPhase('Under Review', [next_phase])

ac_review = ReviewPhase('Under Review', [next_phase])

response = Phase('Ready to Respond', [next_phase])

rejected = Phase('Rejected', [])

accepted = Phase('Accepted', [next_phase])

progress = Phase('Progress', [next_phase])

standard_stage = Stage('Standard', Form(), [internal_review, response, ac_review, response, accepted, rejected])

first_stage = Stage('Standard', Form(), [internal_review, response, progress, rejected])

single_stage = Workflow('Single Stage', [standard_stage])

two_stage = Workflow('Two Stage', [first_stage, standard_stage])
