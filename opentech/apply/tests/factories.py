from django.forms import Form
import factory

from opentech.apply.workflow import Phase, Stage, Workflow


class PhaseFactory(factory.Factory):
    class Meta:
        model = Phase

    name = factory.Faker('word')


class StageFactory(factory.Factory):
    class Meta:
        model = Stage
        inline_args = ('name', 'form', 'phases',)

    class Params:
        num_phases = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    form = factory.LazyFunction(Form)
    phases = factory.LazyAttribute(lambda o: [PhaseFactory() for _ in range(o.num_phases)])


class WorkflowFactory(factory.Factory):
    class Meta:
        model = Workflow
        inline_args = ('name', 'stages',)

    class Params:
        num_stages = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    stages = factory.LazyAttribute(lambda o: [StageFactory() for _ in range(o.num_stages)])
