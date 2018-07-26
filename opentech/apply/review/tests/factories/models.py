from collections import defaultdict

import factory

from opentech.apply.funds.models import AbstractRelatedReviewForm, FundReviewForm
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory, FundTypeFactory
from opentech.apply.review.options import YES, NO, MAYBE
from opentech.apply.users.tests.factories import StaffFactory

from opentech.apply.review.models import Review, ReviewForm
from opentech.apply.review.views import get_fields_for_stage
from opentech.apply.stream_forms.testing.factories import AddFormFieldsMetaclass

from . import blocks

__all__ = ['ReviewFactory', 'ReviewFormFactory', 'AbstractRelatedReviewFormFactory', 'FundReviewFormFactory',
           'ReviewFundTypeFactory', 'ReviewApplicationSubmissionFactory']


def build_form(data, prefix=''):
    if prefix:
        prefix += '__'

    extras = defaultdict(dict)
    for key, value in data.items():
        if 'form_fields' in key:
            _, field, attr = key.split('__')
            extras[field][attr] = value

    form_fields = {}
    for i, field in enumerate(blocks.ReviewFormFieldsFactory.factories):
        form_fields[f'{prefix}form_fields__{i}__{field}__'] = ''
        for attr, value in extras[field].items():
            form_fields[f'{prefix}form_fields__{i}__{field}__{attr}'] = value

    return form_fields


class ReviewFormDataFactory(factory.DictFactory, metaclass=AddFormFieldsMetaclass):
    field_factory = blocks.ReviewFormFieldsFactory

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        submission = kwargs.pop('submission')

        form_fields = {
            field.id: 0
            for field in get_fields_for_stage(submission)
        }

        form_fields.update(**kwargs)
        return super()._build(model_class, *args, **form_fields)


class ReviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = Review

    class Params:
        recommendation_yes = factory.Trait(recommendation=YES)
        recommendation_maybe = factory.Trait(recommendation=MAYBE)
        draft = factory.Trait(is_draft=True)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    author = factory.SubFactory(StaffFactory)
    form_fields = blocks.ReviewFormFieldsFactory
    form_data = factory.SubFactory(ReviewFormDataFactory, form_fields=factory.SelfAttribute('..form_fields'), submission=factory.SelfAttribute('..submission'))
    is_draft = False
    recommendation = NO
    score = 0


class ReviewFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReviewForm

    name = factory.Faker('word')
    form_fields = blocks.ReviewFormFieldsFactory


class AbstractRelatedReviewFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = AbstractRelatedReviewForm
        abstract = True
    form = factory.SubFactory(ReviewFormFactory)


class ReviewFundTypeFactory(FundTypeFactory):

    @factory.post_generation
    def review_forms(self, create, extracted, **kwargs):
        if create:
            fields = build_form(kwargs, prefix='form')
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                FundReviewFormFactory(
                    fund=self,
                    **fields
                )


class FundReviewFormFactory(AbstractRelatedReviewFormFactory):
    class Meta:
        model = FundReviewForm
    fund = factory.SubFactory(ReviewFundTypeFactory, parent=None)


class ReviewApplicationSubmissionFactory(ApplicationSubmissionFactory):
    page = factory.SubFactory(ReviewFundTypeFactory)
