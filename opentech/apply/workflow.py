from typing import Iterator, Iterable, Sequence, Union

from django.forms import Form


class Workflow(Iterable['Stage']):
    def __init__(self, name: str, stages: Sequence['Stage']) -> None:
        self.name = name
        self.stages = stages

    def __iter__(self) -> Iterator['Stage']:
        yield from self.stages

    def next(self, current_stage: Union['Stage', None]=None) -> Union['Stage', None]:
        if not current_stage:
            return self.stages[0]

        for i, stage in enumerate(self):
            if stage == current_stage:
                try:
                    return self.stages[i + 1]
                except IndexError:
                    pass

        return None


class Stage:
    def __init__(self, name: str, form: Form) -> None:
        self.name = name
        self.form = form
