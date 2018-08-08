from collections import defaultdict
import datetime

import factory
import wagtail_factories

from opentech.apply.funds.models import (
    ApplicationSubmission,
    ApplicationRevision,
    FundType,
    LabType,
    RequestForPartners,
    Round,
    SealedRound,
)
from opentech.apply.funds.models.forms import (
    ApplicationForm,
    ApplicationBaseForm,
    LabBaseForm,
    RoundBaseForm,
)
from opentech.apply.users.tests.factories import StaffFactory, UserFactory
from opentech.apply.stream_forms.testing.factories import FormDataFactory
from opentech.apply.home.factories import ApplyHomePageFactory

from . import blocks


__all__ = [
    'FundTypeFactory',
    'ApplicationBaseFormFactory',
    'ApplicationFormFactory',
    'ApplicationRevisionFactory',
    'ApplicationSubmissionFactory',
    'RoundFactory',
    'RoundBaseFormFactory',
    'LabFactory',
    'LabBaseFormFactory',
    'SealedRoundFactory',
    'SealedSubmissionFactory',
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
    def parent(self, create, extracted_parent, **parent_kwargs):
        # THIS MUST BE THE FIRST POST GENERATION METHOD OR THE OBJECT WILL BE UNSAVED
        if create:
            if extracted_parent and parent_kwargs:
                raise ValueError('Cant pass a parent instance and attributes')

            if not extracted_parent:
                parent = ApplyHomePageFactory(**parent_kwargs)
            else:
                # Assume root node if no parent passed
                parent = extracted_parent

            parent.add_child(instance=self)

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            from opentech.apply.review.tests.factories.models import build_form as review_build_form, ReviewFormFactory
            fields = build_form(kwargs, prefix='form')
            review_fields = review_build_form(kwargs)
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                ApplicationBaseFormFactory(
                    application=self,
                    **fields,
                )
                ReviewFormFactory(**review_fields)


class RequestForPartnersFactory(FundTypeFactory):
    class Meta:
        model = RequestForPartners


class AbstractRelatedFormFactory(factory.DjangoModelFactory):
    class Meta:
        abstract = True
    form = factory.SubFactory('opentech.apply.funds.tests.factories.ApplicationFormFactory')


class ApplicationBaseFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = ApplicationBaseForm
    application = factory.SubFactory(FundTypeFactory)


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
    start_date = factory.Sequence(lambda n: datetime.date.today() + datetime.timedelta(days=7 * n + 1))
    end_date = factory.Sequence(lambda n: datetime.date.today() + datetime.timedelta(days=7 * (n + 1)))
    lead = factory.SubFactory(StaffFactory)

    @factory.post_generation
    def forms(self, create, extracted, **kwargs):
        if create:
            fields = build_form(kwargs, prefix='form')
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                RoundBaseFormFactory(
                    round=self,
                    **fields,
                )


class SealedRoundFactory(RoundFactory):
    class Meta:
        model = SealedRound


class TodayRoundFactory(RoundFactory):
    start_date = factory.LazyFunction(datetime.date.today)
    end_date = factory.LazyFunction(lambda: datetime.date.today() + datetime.timedelta(days=7))


class RoundBaseFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = RoundBaseForm
    round = factory.SubFactory(RoundFactory)


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
                LabBaseFormFactory(
                    lab=self,
                    **fields,
                )


class LabBaseFormFactory(AbstractRelatedFormFactory):
    class Meta:
        model = LabBaseForm
    lab = factory.SubFactory(LabFactory)


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

    @factory.post_generation
    def reviewers(self, create, reviewers, **kwargs):
        if create and reviewers:
            self.reviewers.set(reviewers)

    @classmethod
    def _generate(cls, strat, params):
        params.update(**build_form(params))
        return super()._generate(strat, params)


class SealedSubmissionFactory(ApplicationSubmissionFactory):
    page = factory.SubFactory(RequestForPartnersFactory)
    round = factory.SubFactory(
        SealedRoundFactory,
        workflow_name=factory.SelfAttribute('..workflow_name'),
        lead=factory.SelfAttribute('..lead'),
        now=True,
    )


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
