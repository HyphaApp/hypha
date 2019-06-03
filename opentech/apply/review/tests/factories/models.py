import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory, AssignedReviewersFactory
from opentech.apply.stream_forms.testing.factories import FormDataFactory

from ...options import YES, NO, MAYBE, AGREE, DISAGREE, PRIVATE, REVIEWER
from ...models import Review, ReviewForm, ReviewOpinion

from . import blocks

__all__ = ['ReviewFactory', 'ReviewFormFactory', 'ReviewOpinionFactory']


class ReviewFormDataFactory(FormDataFactory):
    field_factory = blocks.ReviewFormFieldsFactory


class ReviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = Review

    class Params:
        recommendation_yes = factory.Trait(recommendation=YES)
        recommendation_maybe = factory.Trait(recommendation=MAYBE)
        draft = factory.Trait(is_draft=True)
        visibility_private = factory.Trait(visibility=PRIVATE)
        visibility_reviewer = factory.Trait(visibility=REVIEWER)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    revision = factory.SelfAttribute('submission.live_revision')
    author = factory.SubFactory(AssignedReviewersFactory, submission=factory.SelfAttribute('..submission'))
    form_fields = factory.LazyAttribute(lambda o: o.submission.round.review_forms.first().fields)
    form_data = factory.SubFactory(
        ReviewFormDataFactory,
        form_fields=factory.SelfAttribute('..form_fields'),
    )
    is_draft = False
    recommendation = NO
    score = 0


class ReviewOpinionFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReviewOpinion

    class Params:
        opinion_agree = factory.Trait(opinion=AGREE)
        opinion_disagree = factory.Trait(opinion=DISAGREE)

    review = factory.SubFactory(ReviewFactory)
    author = factory.SubFactory(AssignedReviewersFactory, staff=True, submission=factory.SelfAttribute('..review.submission'))
    opinion = DISAGREE


class ReviewFormFactory(factory.DjangoModelFactory):
    class Meta:
        model = ReviewForm

    name = factory.Faker('word')
    form_fields = blocks.ReviewFormFieldsFactory
