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

    def next(self, current_phase: Union['Phase', str]=None) -> Union['Phase', None]:
        stage_idx, phase_idx = self.current_index(current_phase)
        try:
            return self.stages[stage_idx].phases[phase_idx + 1]
        except IndexError:
            try:
                return self.stages[stage_idx + 1].phases[0]
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
    def __init__(self, name: str) -> None:
        self.name = name
        self.stage: Union['Stage', None] = None
        self.occurance = 0

    def __str__(self):
        return '__'.join([self.stage.name, self.name, str(self.occurance)])


# --- OTF Workflow ---

class ReviewPhase(Phase):
    pass


internal_review = ReviewPhase('Under Review')

ac_review = ReviewPhase('Under Review')

response = Phase('Ready to Respond')

rejected = Phase('Rejected')

accepted = Phase('Accepted')

progress = Phase('Progress')

standard_stage = Stage('Standard', Form(), [internal_review, response, ac_review, response, accepted, rejected])

first_stage = Stage('Standard', Form(), [internal_review, response, progress, rejected])

single_stage = Workflow('Single Stage', [standard_stage])

two_stage = Workflow('Two Stage', [first_stage, standard_stage])
