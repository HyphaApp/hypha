import json
import random

import factory

from hypha.apply.review import blocks
from hypha.apply.review.options import MAYBE, NO, PRIVATE, REVIEWER, YES
from hypha.apply.stream_forms.testing.factories import (
    CharFieldBlockFactory,
    FormFieldBlockFactory,
    StreamFieldUUIDFactory,
)
from hypha.apply.utils.testing.factories import RichTextFieldBlockFactory

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


class VisibilityBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.VisibilityBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return random.choices([PRIVATE, REVIEWER])


class ScoreFieldWithoutTextBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ScoreFieldWithoutTextBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return random.randint(1, 5)


class ScoreFieldBlockFactory(FormFieldBlockFactory):
    class Meta:
        model = blocks.ScoreFieldBlock

    @classmethod
    def make_answer(cls, params=dict()):
        return json.dumps([random.randint(1, 5), factory.Faker('paragraph').generate(params)])

    @classmethod
    def make_form_answer(cls, params=dict()):
        defaults = {
            'score': random.randint(1, 5),
            'description': factory.Faker('paragraph').generate({}),
        }
        defaults.update(params)
        return defaults


ReviewFormFieldsFactory = StreamFieldUUIDFactory({
    'char': CharFieldBlockFactory,
    'text': RichTextFieldBlockFactory,
    'score': ScoreFieldBlockFactory,
    'score_without_text': ScoreFieldWithoutTextBlockFactory,
    'recommendation': RecommendationBlockFactory,
    'comments': RecommendationCommentsBlockFactory,
    'visibility': VisibilityBlockFactory,
})
