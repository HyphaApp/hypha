from django.forms import Form
import factory

from .workflow import Stage, Workflow


class StageFactory(factory.Factory):
    class Meta:
        model = Stage

    name = factory.Faker('word')
    form = factory.LazyFunction(Form)


class WorkflowFactory(factory.Factory):
    class Meta:
        model = Workflow
        inline_args = ('name', 'stages',)

    class Params:
        num_stages = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    stages = factory.LazyAttribute(lambda o: [StageFactory() for _ in range(o.num_stages)])
