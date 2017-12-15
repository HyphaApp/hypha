from django.forms import Form
import factory

from opentech.apply.workflow import Action, Phase, Stage, Workflow


class ListSubFactory(factory.SubFactory):
    def __init__(self, *args, count=0, **kwargs):
        self.count = count
        super().__init__(*args, **kwargs)

    def evaluate(self, *args, **kwargs):
        if isinstance(self.count, factory.declarations.BaseDeclaration):
            self.evaluated_count = self.count.evaluate(*args, **kwargs)
        else:
            self.evaluated_count = self.count

        return super().evaluate(*args, **kwargs)

    def generate(self, step, params):
        subfactory = self.get_factory()
        force_sequence = step.sequence if self.FORCE_SEQUENCE else None
        return [
            step.recurse(subfactory, params, force_sequence=force_sequence)
            for _ in range(self.evaluated_count)
        ]


class ActionFactory(factory.Factory):
    class Meta:
        model = Action

    name = factory.Faker('word')


class PhaseFactory(factory.Factory):
    class Meta:
        model = Phase

    class Params:
        num_actions = factory.Faker('random_int', min=1, max=5)

    name = factory.Faker('word')
    actions = ListSubFactory(ActionFactory, count=factory.SelfAttribute('num_actions'))


class StageFactory(factory.Factory):
    class Meta:
        model = Stage
        inline_args = ('name', 'form', 'phases',)

    class Params:
        num_phases = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    form = factory.LazyFunction(Form)
    phases = ListSubFactory(PhaseFactory, count=factory.SelfAttribute('num_phases'))


class WorkflowFactory(factory.Factory):
    class Meta:
        model = Workflow
        inline_args = ('name', 'stages',)

    class Params:
        num_stages = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    stages = ListSubFactory(StageFactory, count=factory.SelfAttribute('num_stages'))
