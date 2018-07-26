from collections import defaultdict
import datetime
import json

import factory
import wagtail_factories

from opentech.apply.funds.models import (
    AbstractRelatedForm,
    ApplicationForm,
    ApplicationSubmission,
    ApplicationRevision,
    FundType,
    FundForm,
    LabForm,
    LabType,
    Round,
    RoundForm,
)
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from opentech.apply.stream_forms.testing.factories import FormDataFactory

from . import blocks


__all__ = [
    'FundTypeFactory',
    'FundFormFactory',
    'ApplicationFormFactory',
    'ApplicationRevisionFactory',
    'ApplicationSubmissionFactory',
    'RoundFactory',
    'RoundFormFactory',
    'LabFactory',
    'LabFormFactory',
]


def build_form(data, prefix=''):
    if prefix:
        prefix += '__'

    extras = defaultdict(dict)
    for key, value in data.items():
        if 'form_fields' in key:
            _, field, attr = key.split('__')
            extras[field][attr] = value

    form_fields = {}
    for i, field in enumerate(blocks.CustomFormFieldsFactory.factories):
        form_fields[f'{prefix}form_fields__{i}__{field}__'] = ''
        for attr, value in extras[field].items():
            form_fields[f'{prefix}form_fields__{i}__{field}__{attr}'] = value

    return form_fields


class FundTypeFactory(wagtail_factories.PageFactory):
    class Meta:
        model = FundType

    class Params:
        workflow_stages = 1

    # Will need to update how the stages are identified as Fund Page changes
    workflow_name = factory.LazyAttribute(lambda o: list(FundType.WORKFLOW_CHOICES.keys())[o.workflow_stages - 1])

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            from opentech.apply.review.tests.factories.models import build_form as review_build_form, ReviewFormFactory
            fields = build_form(kwargs, prefix='form')
            review_fields = review_build_form(kwargs)
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                FundFormFactory(
                    fund=self,
                    **fields,
                )
                ReviewFormFactory(**review_fields)


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

    class Params:
        now = factory.Trait(
            start_date=factory.LazyFunction(datetime.date.today),
            end_date=factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7)),
        )

    title = factory.Sequence('Round {}'.format)
    start_date = factory.Sequence(lambda n: datetime.date.today() + datetime.timedelta(days=7 * n))
    end_date = factory.Sequence(lambda n: datetime.date.today() + datetime.timedelta(days=7 * (n + 1)))
    lead = factory.SubFactory(StaffFactory)

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            fields = build_form(kwargs, prefix='form')
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                RoundFormFactory(
                    round=self,
                    **fields,
                )


class TodayRoundFactory(RoundFactory):
    start_date = factory.LazyFunction(datetime.date.today)
    end_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))


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
    workflow_name = factory.LazyAttribute(lambda o: list(FundType.WORKFLOW_CHOICES.keys())[o.workflow_stages - 1])
    lead = factory.SubFactory(StaffFactory)

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            fields = build_form(kwargs, prefix='form')
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                LabFormFactory(
                    lab=self,
                    **fields,
                )


class LabFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = LabForm
    lab = factory.SubFactory(LabFactory, parent=None)


class ApplicationFormDataFactory(FormDataFactory):
    field_factory = blocks.CustomFormFieldsFactory


class ApplicationSubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationSubmission

    class Params:
        workflow_stages = 1
        draft_proposal = factory.Trait(
            status='draft_proposal',
            workflow_name='double',
        )

    form_fields = blocks.CustomFormFieldsFactory
    form_data = factory.SubFactory(
        ApplicationFormDataFactory,
        form_fields=factory.SelfAttribute('..form_fields'),
    )
    page = factory.SubFactory(FundTypeFactory)
    workflow_name = factory.LazyAttribute(lambda o: list(FundType.WORKFLOW_CHOICES.keys())[o.workflow_stages - 1])
    round = factory.SubFactory(
        RoundFactory,
        workflow_name=factory.SelfAttribute('..workflow_name'),
        lead=factory.SelfAttribute('..lead'),
    )
    user = factory.SubFactory(UserFactory)
    lead = factory.SubFactory(StaffFactory)
    live_revision = None
    draft_revision = None

    @classmethod
    def _generate(cls, strat, params):
        params.update(**build_form(params))
        return super()._generate(strat, params)


class ApplicationRevisionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ApplicationRevision

    submission = factory.SubFactory('opentech.apply.funds.tests.factories.ApplicationSubmissionFactory')
    form_data = factory.SubFactory(
        ApplicationFormDataFactory,
        form_fields=factory.SelfAttribute('..submission.form_fields'),
        for_factory=ApplicationSubmissionFactory,
        clean=True,
    )
