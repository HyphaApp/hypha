import datetime

import factory
import wagtail_factories

from opentech.apply.funds.models import (
    AbstractRelatedForm,
    ApplicationSubmission,
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
    'ApplicationSubmissionFactory',
    'RoundFactory',
    'RoundFormFactory',
    'LabFactory',
    'LabFormFactory',
]


def build_form(prefix=''):
    if prefix:
        prefix += '__'
    return {
        f'{prefix}form_fields__{i}__{field}__': ''
        for i, field in enumerate(blocks.CustomFormFieldsFactory.factories.keys())
    }


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
            fields = build_form(prefix='form')
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
    start_date = factory.Sequence(lambda s: datetime.date.today() + datetime.timedelta(days=s))
    end_date = factory.LazyAttribute(lambda o: o.start_date + datetime.timedelta(days=1))
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


class ApplicationSubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationSubmission

    form_fields = blocks.CustomFormFieldsFactory
    page = factory.SubFactory(FundTypeFactory)
    round = factory.SubFactory(RoundFactory)

    @classmethod
    def _generate(cls, strat, params):
        params.update(**build_form())
        return super()._generate(strat, params)

    @classmethod
    def _create(cls, model, *args, **kwargs):
        # Make sure we have form_data so no error
        kwargs['form_data'] = {}
        return super()._create(model, *args, **kwargs)

    @factory.post_generation
    def form_data(self, create, extracted, **kwargs):
        if not extracted:
            # Ids are added but are not available in the cached version
            self.refresh_from_db()
            form_data = {}
            for field in self.form_fields:
                try:
                    answer = kwargs[field.block_type]
                except KeyError:
                    answer = ''
                form_data[field.id] = answer

            self.form_data = form_data
            self.save()
