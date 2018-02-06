import datetime

from django.forms import Form
import factory
import wagtail_factories

from opentech.apply.funds.models import (
    ApplicationForm,
    FundType,
    FundForm,
    LabForm,
    LabType,
    Round,
)
from opentech.apply.funds.workflow import Action, Phase, Stage, Workflow

from . import blocks


__all__ = [
    'ActionFactory',
    'PhaseFactory',
    'StageFactory',
    'WorkflowFactory',
    'FundTypeFactory',
    'FundFormFactory',
    'ApplicationFormFactory',
    'RoundFactory',
    'LabFactory',
    'LabFormFactory',
]


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
    stage = factory.PostGeneration(
        lambda obj, create, extracted, **kwargs: StageFactory.build(phases=[obj])
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        actions = kwargs.pop('actions')
        new_class = type(model_class.__name__, (model_class,), {'actions': actions})
        return new_class(*args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        # defer to create because parent uses build
        return cls._create(model_class, *args, **kwargs)


class StageFactory(factory.Factory):
    class Meta:
        model = Stage
        inline_args = ('form',)

    class Params:
        num_phases = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    form = factory.LazyFunction(Form)
    phases = ListSubFactory(PhaseFactory, count=factory.SelfAttribute('num_phases'))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Returns a new class
        phases = kwargs.pop('phases')
        name = kwargs.pop('name')
        return type(model_class.__name__, (model_class,), {'phases': phases, 'name': name})

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        # returns an instance of the stage class
        phases = kwargs.pop('phases')
        name = kwargs.pop('name')
        new_class = type(model_class.__name__, (model_class,), {'phases': phases, 'name': name})
        return new_class(*args, **kwargs)


class WorkflowFactory(factory.Factory):
    class Meta:
        model = Workflow
        rename = {'stages': 'stage_classes'}

    class Params:
        num_stages = factory.Faker('random_int', min=1, max=3)

    name = factory.Faker('word')
    stages = ListSubFactory(StageFactory, count=factory.SelfAttribute('num_stages'))

    @factory.LazyAttribute
    def forms(self):
        return [Form() for _ in range(self.num_stages)]

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        name = kwargs.pop('name')
        stages = kwargs.pop('stage_classes')
        new_class = type(model_class.__name__, (model_class,), {'name': name, 'stage_classes': stages})
        return new_class(*args, **kwargs)


class FundTypeFactory(wagtail_factories.PageFactory):
    class Meta:
        model = FundType

    class Params:
        workflow_stages = 1
        number_forms = 1

    # Will need to update how the stages are identified as Fund Page changes
    workflow = factory.LazyAttribute(lambda o: list(FundType.WORKFLOWS.keys())[o.workflow_stages - 1])


class FundFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = FundForm
    fund = factory.SubFactory(FundTypeFactory, parent=None)
    form = factory.SubFactory('opentech.apply.tests.factories.ApplicationFormFactory')


class ApplicationFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationForm

    name = factory.Faker('word')
    form_fields = wagtail_factories.StreamFieldFactory({
        'email': blocks.EmailBlockFactory,
        'full_name': blocks.FullNameBlockFactory,
    })


class RoundFactory(wagtail_factories.PageFactory):
    class Meta:
        model = Round

    title = factory.Sequence('Round {}'.format)
    start_date = factory.LazyFunction(datetime.date.today)
    end_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))


class LabFactory(wagtail_factories.PageFactory):
    class Meta:
        model = LabType

    class Params:
        workflow_stages = 1
        number_forms = 1

    # Will need to update how the stages are identified as Fund Page changes
    workflow = factory.LazyAttribute(lambda o: list(FundType.WORKFLOWS.keys())[o.workflow_stages - 1])


class LabFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = LabForm
    lab = factory.SubFactory(LabFactory, parent=None)
    form = factory.SubFactory('opentech.apply.tests.factories.ApplicationFormFactory')
