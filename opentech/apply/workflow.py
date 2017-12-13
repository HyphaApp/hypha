from typing import Iterator, Iterable

from django.forms import Form


class Workflow(Iterable['Stage']):
    def __init__(self, name: str, *stages: 'Stage') -> None:
        self.name = name
        if not stages:
            raise ValueError('Stages must be supplied')
        self.stages = stages

    def __iter__(self) -> Iterator['Stage']:
        yield from self.stages


class Stage:
    def __init__(self, name: str, form: Form) -> None:
        self.name = name
        self.form = form
