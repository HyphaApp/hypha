import datetime

import factory
import wagtail_factories

from opentech.apply.funds.models import (
    AbstractRelatedForm,
    ApplicationForm,
    FundType,
    FundForm,
    LabForm,
    LabType,
    Round,
    RoundForm,
)
from opentech.apply.users.tests.factories import UserFactory
from opentech.apply.users.groups import STAFF_GROUP_NAME

from . import blocks


__all__ = [
    'FundTypeFactory',
    'FundFormFactory',
    'ApplicationFormFactory',
    'RoundFactory',
    'RoundFormFactory',
    'LabFactory',
    'LabFormFactory',
]


class FundTypeFactory(wagtail_factories.PageFactory):
    class Meta:
        model = FundType

    class Params:
        workflow_stages = 1

    # Will need to update how the stages are identified as Fund Page changes
    workflow_name = factory.LazyAttribute(lambda o: list(FundType.WORKFLOWS.keys())[o.workflow_stages - 1])

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            fields = {
                f'form__form_fields__{i}__{field}__': ''
                for i, field in enumerate(blocks.CustomFormFieldsFactory.factories.keys())
            }
            fields.update(**kwargs)
            for _ in range(len(self.workflow_class.stage_classes)):
                # Generate a form based on all defined fields on the model
                FundFormFactory(
                    fund=self,
                    **fields,
                )


class AbstractRelatedFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = AbstractRelatedForm
        abstract = True
    form = factory.SubFactory('opentech.apply.funds.tests.factories.ApplicationFormFactory')


class FundFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = FundForm
    fund = factory.SubFactory(FundTypeFactory, parent=None)


class ApplicationFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationForm

    name = factory.Faker('word')
    form_fields = blocks.CustomFormFieldsFactory


class RoundFactory(wagtail_factories.PageFactory):
    class Meta:
        model = Round

    title = factory.Sequence('Round {}'.format)
    start_date = factory.LazyFunction(datetime.date.today)
    end_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))
    lead = factory.SubFactory(UserFactory, groups__name=STAFF_GROUP_NAME)


class RoundFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = RoundForm
    round = factory.SubFactory(RoundFactory, parent=None)


class LabFactory(wagtail_factories.PageFactory):
    class Meta:
        model = LabType

    class Params:
        workflow_stages = 1
        number_forms = 1

    # Will need to update how the stages are identified as Fund Page changes
    workflow_name = factory.LazyAttribute(lambda o: list(FundType.WORKFLOWS.keys())[o.workflow_stages - 1])


class LabFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = LabForm
    lab = factory.SubFactory(LabFactory, parent=None)
