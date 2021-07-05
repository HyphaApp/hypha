import uuid

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.text import slugify

from ..groups import (
    APPLICANT_GROUP_NAME,
    APPROVER_GROUP_NAME,
    COMMUNITY_REVIEWER_GROUP_NAME,
    FINANCE_GROUP_NAME,
    PARTNER_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
)


class GroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.Sequence('group name {}'.format)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.LazyAttribute(lambda o: '{}+{}@email.com'.format(slugify(o.full_name), uuid.uuid4()))
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


class StaffFactory(OAuthUserFactory):
    class Meta:
        exclude = ('slack_temp', )
    is_staff = True

    # Required to generate the fake data add pass to LazyAttribute
    slack_temp = factory.Faker('word')

    slack = factory.LazyAttribute(lambda p: '@{}'.format(p.slack_temp))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=STAFF_GROUP_NAME))


class FinanceFactory(OAuthUserFactory):
    class Meta:
        exclude = ('slack_temp', )
    is_staff = True

    # Required to generate the fake data add pass to LazyAttribute
    slack_temp = factory.Faker('word')

    slack = factory.LazyAttribute(lambda p: '@{}'.format(p.slack_temp))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=FINANCE_GROUP_NAME))


class ApproverFactory(StaffFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(
                GroupFactory(name=STAFF_GROUP_NAME),
                GroupFactory(name=APPROVER_GROUP_NAME),
            )


class SuperUserFactory(StaffFactory):
    is_superuser = True


class ReviewerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=REVIEWER_GROUP_NAME))


class ApplicantFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=APPLICANT_GROUP_NAME))


class CommunityReviewerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=COMMUNITY_REVIEWER_GROUP_NAME))


class PartnerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=PARTNER_GROUP_NAME))
