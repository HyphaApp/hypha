import factory

from ...workflow import Phase, Stage, Workflow, no_permissions


class StageFactory(factory.Factory):
    class Meta:
        model = Stage

    name = factory.Faker('word')

    @classmethod
    def create(cls, **kwargs):
        return super().create(**kwargs)


class PhaseFactory(factory.Factory):
    class Meta:
        model = Phase

    name = factory.Faker('word')
    display = factory.SelfAttribute('.name')
    stage = factory.SubFactory(StageFactory)
    permissions = no_permissions
    step = factory.Sequence(lambda i: i)


class PhasesFactory(factory.Factory):
    class Meta:
        model = PhaseFactory

    count = 1

    @classmethod
    def create(cls, *args, **kwargs):
        print(args)
        print(kwargs)
        return super().create(*args, **kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        count = kwargs.pop('count')
        print(kwargs)
        return [
            model_class(*args, **kwargs)
            for _ in range(count)
        ]


class WorkflowFactory(factory.Factory):
    class Meta:
        model = Workflow
        inline_args = ('name', 'admin_name')

    name = factory.Faker('word')
    admin_name = factory.SelfAttribute('.name')
    phases = factory.SubFactory(PhasesFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        phases = kwargs.pop('phases')
        phases = {phase.name: phase for phase in phases}
        return super()._create(model_class, *args, **phases, **kwargs)
