from typing import Iterator, Iterable, Sequence, Union

from django.forms import Form


class Workflow:
    def __init__(self, name: str, stages: Sequence['Stage']) -> None:
        self.name = name
        self.stages = stages
        self.mapping = {
            str(phase): (i, j)
            for i, stage in enumerate(stages)
            for j, phase in enumerate(stage)
        }

    def current_index(self, phase: Union['Phase', str, None]):
        if isinstance(phase, Phase):
            phase = str(phase)
        try:
            return self.mapping[phase]
        except KeyError:
            return 0, -1

    def next(self, current_phase: Union['Phase', str, None]=None) -> Union['Phase', None]:
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
                 current_phase: Union['Phase', None]=None
    ) -> None:
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

    def __str__(self):
        return '__'.join([self.stage.name, self.name])
