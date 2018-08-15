import json
import random
import factory

from opentech.apply.review import blocks
from opentech.apply.review.options import YES, MAYBE, NO
from opentech.apply.stream_forms.testing.factories import FormFieldBlockFactory, CharFieldBlockFactory, \
    StreamFieldUUIDFactory
from opentech.apply.utils.testing.factories import RichTextFieldBlockFactory

__all__ = ['ReviewFormFieldsFactory', 'RecommendationBlockFactory', 'ScoreFieldBlockFactory']


class RecommendationBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RecommendationBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return random.choices([NO, MAYBE, YES])


class RecommendationCommentsBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.RecommendationCommentsBlock


class ScoreFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ScoreFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return json.dumps([factory.Faker('paragraph').generate(params), random.randint(1, 5)])

    @classmethod
    def make_form_answer(cls, params=dict()):
        return {
            'description': factory.Faker('paragraph').generate(params),
            'score': random.randint(1, 5),
        }


ReviewFormFieldsFactory = StreamFieldUUIDFactory({
    'char': CharFieldBlockFactory,
    'text': RichTextFieldBlockFactory,
    'score': ScoreFieldBlockFactory,
    'recommendation': RecommendationBlockFactory,
    'comments': RecommendationCommentsBlockFactory,
})
