import factory

from opentech.apply.funds.models.forms import ApplicationBaseReviewForm
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory, FundTypeFactory
from opentech.apply.stream_forms.testing.factories import AddFormFieldsMetaclass
from opentech.apply.users.tests.factories import StaffFactory

from ...options import YES, NO, MAYBE
from ...models import Review, ReviewForm
from ...views import get_fields_for_stage

from . import blocks

__all__ = ['ReviewFactory', 'ReviewFormFactory',
           'ApplicationBaseReviewFormFactory', 'ReviewFundTypeFactory',
           'ReviewApplicationSubmissionFactory']


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
    form_data = factory.SubFactory(
        ReviewFormDataFactory,
        form_fields=factory.SelfAttribute('..form_fields'),
        submission=factory.SelfAttribute('..submission'),
    )
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
        abstract = True
    form = factory.SubFactory(ReviewFormFactory)


class ReviewFundTypeFactory(FundTypeFactory):

    @factory.post_generation
    def review_forms(self, create, extracted, **kwargs):
        if create:
            for _ in self.workflow.stages:
                # Generate a form based on all defined fields on the model
                ApplicationBaseReviewFormFactory(
                    application=self,
                    **kwargs
                )


class ApplicationBaseReviewFormFactory(AbstractRelatedReviewFormFactory):
    class Meta:
        model = ApplicationBaseReviewForm
    application = factory.SubFactory(ReviewFundTypeFactory, parent=None)


class ReviewApplicationSubmissionFactory(ApplicationSubmissionFactory):
    page = factory.SubFactory(ReviewFundTypeFactory)
