import factory

from opentech.apply.activity.models import Activity, Event, INTERNAL, MESSAGES, REVIEWER
from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.users.tests.factories import UserFactory


class CommentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Activity

    class Params:
        internal = factory.Trait(visibility=INTERNAL)
        reviewers = factory.Trait(visibility=REVIEWER)

    submission = factory.SubFactory(ApplicationSubmissionFactory)
    user = factory.SubFactory(UserFactory)
    message = factory.Faker('sentence')

    @classmethod
    def _get_manager(cls, model_class):
        return model_class.comments


class EventFactory(factory.DjangoModelFactory):
    class Meta:
        model = Event

    type = factory.Iterator([choice[0] for choice in MESSAGES.choices()])
    by = factory.SubFactory(UserFactory)
    submission = factory.SubFactory(ApplicationSubmissionFactory)
