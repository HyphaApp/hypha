import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.stream_forms.testing.factories import AddFormFieldsMetaclass
from opentech.apply.users.tests.factories import StaffFactory

from ...options import YES, NO, MAYBE
from ...models import Review, ReviewForm

from . import blocks

__all__ = ['ReviewFactory', 'ReviewFormFactory']


class ReviewFormDataFactory(factory.DictFactory, metaclass=AddFormFieldsMetaclass):
    field_factory = blocks.ReviewFormFieldsFactory


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
    form_data = factory.SubFactory(
        ReviewFormDataFactory,
        form_fields=factory.SelfAttribute('..form_fields'),
    )
    is_draft = False
    recommendation = NO
    score = 0


class ReviewFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReviewForm

    name = factory.Faker('word')
    form_fields = blocks.ReviewFormFieldsFactory
