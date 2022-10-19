import uuid

import factory
from django.utils import timezone

from hypha.apply.activity.models import (
    MESSAGES,
    REVIEWER,
    TEAM,
    Activity,
    Event,
    Message,
)
from hypha.apply.funds.tests.factories import ApplicationSubmissionFactory
from hypha.apply.users.tests.factories import UserFactory


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Activity

    class Params:
        internal = factory.Trait(visibility=TEAM)
        reviewers = factory.Trait(visibility=REVIEWER)

    source = factory.SubFactory(ApplicationSubmissionFactory)
    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence')
    timestamp = factory.LazyFunction(timezone.now)


class CommentFactory(ActivityFactory):
    @classmethod
    def _get_manager(cls, model_class):
        return model_class.comments


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event

    type = factory.Iterator([choice[0] for choice in MESSAGES.choices])
    by = factory.SubFactory(UserFactory)
    source = factory.SubFactory(ApplicationSubmissionFactory)


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    type = 'Email'
    content = factory.Faker('sentence')
    recipient = factory.Faker('email')
    event = factory.SubFactory(EventFactory)
    external_id = factory.LazyFunction(lambda: '<{}>'.format(uuid.uuid4()))
