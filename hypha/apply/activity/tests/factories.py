import uuid

import factory
from django.utils import timezone

from opentech.apply.activity.models import Activity, Event, TEAM, Message, MESSAGES, REVIEWER
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory


class CommentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Activity

    class Params:
        internal = factory.Trait(visibility=TEAM)
        reviewers = factory.Trait(visibility=REVIEWER)

    source = factory.SubFactory(ApplicationSubmissionFactory)
    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence')
    timestamp = factory.LazyFunction(timezone.now)

    @classmethod
    def _get_manager(cls, model_class):
        return model_class.comments


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = Event

    type = factory.Iterator([choice[0] for choice in MESSAGES.choices()])
    by = factory.SubFactory(UserFactory)
    source = factory.SubFactory(ApplicationSubmissionFactory)


class MessageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Message

    type = 'Email'
    content = factory.Faker('sentence')
    recipient = factory.Faker('email')
    event = factory.SubFactory(EventFactory)
    external_id = factory.LazyFunction(lambda: '<{}>'.format(uuid.uuid4()))
