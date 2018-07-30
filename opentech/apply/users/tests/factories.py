from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

import factory

from ..groups import REVIEWER_GROUP_NAME, STAFF_GROUP_NAME


class GroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.Sequence('group name {}'.format)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence('email{}@email.com'.format)
    full_name = factory.Faker('name')
    password = factory.PostGenerationMethodCall('set_password', 'defaultpassword')

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            if not extracted:
                groups = GroupFactory(**kwargs)
            else:
                groups = extracted

            self.groups.add(groups)


class OAuthUserFactory(UserFactory):
    password = factory.PostGenerationMethodCall('set_unusable_password')


class AdminFactory(UserFactory):
    is_admin = True


class StaffFactory(UserFactory):
    class Meta:
        exclude = ('slack_temp', )

    # Required to generate the fake data add pass to LazyAttribute
    slack_temp = factory.Faker('word')

    slack = factory.LazyAttribute(lambda p: '@{}'.format(p.slack_temp))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=STAFF_GROUP_NAME))


class ReviewerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=REVIEWER_GROUP_NAME))
