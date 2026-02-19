import uuid

import factory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils.text import slugify

from ..roles import (
    APPLICANT_GROUP_NAME,
    APPROVER_GROUP_NAME,
    COMMUNITY_REVIEWER_GROUP_NAME,
    CONTRACTING_GROUP_NAME,
    FINANCE_GROUP_NAME,
    PARTNER_GROUP_NAME,
    REVIEWER_GROUP_NAME,
    STAFF_GROUP_NAME,
)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Group
        skip_postgeneration_save = True
        django_get_or_create = ("name",)

    name = factory.Sequence("group name {}".format)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    email = factory.LazyAttribute(
        lambda o: "{}+{}@email.com".format(slugify(o.full_name), uuid.uuid4())
    )
    full_name = factory.Faker("name")
    password = factory.PostGenerationMethodCall("set_password", "defaultpassword")

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            if not extracted:
                groups = GroupFactory(**kwargs)
            else:
                groups = extracted

            self.groups.add(groups)
            self.save()


class OAuthUserFactory(UserFactory):
    password = factory.PostGenerationMethodCall("set_unusable_password")

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        if create:
            self.save()


class AdminFactory(UserFactory):
    is_superuser = True


class StaffFactory(OAuthUserFactory):
    class Meta:
        exclude = ("slack_temp",)

    is_staff = True

    # Required to generate the fake data add pass to LazyAttribute
    slack_temp = factory.Faker("word")

    slack = factory.LazyAttribute(lambda p: "@{}".format(p.slack_temp))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=STAFF_GROUP_NAME))
            self.save()


def get_wagtail_admin_access_permission():
    return Permission.objects.get(
        content_type__app_label="wagtailadmin", codename="access_admin"
    )


class StaffWithWagtailAdminAccessFactory(StaffFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            modifiedStaffGroup = GroupFactory(name=STAFF_GROUP_NAME)
            wagtail_admin_access_permission = get_wagtail_admin_access_permission()
            modifiedStaffGroup.permissions.add(wagtail_admin_access_permission)
            self.groups.add(modifiedStaffGroup)
            self.save()


class StaffWithoutWagtailAdminAccessFactory(StaffFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            modifiedStaffGroup = GroupFactory(name=STAFF_GROUP_NAME)
            wagtail_admin_access_permission = get_wagtail_admin_access_permission()
            modifiedStaffGroup.permissions.remove(wagtail_admin_access_permission)
            self.groups.add(modifiedStaffGroup)
            self.save()


class FinanceFactory(OAuthUserFactory):
    class Meta:
        exclude = ("slack_temp",)

    is_staff = True

    # Required to generate the fake data add pass to LazyAttribute
    slack_temp = factory.Faker("word")

    slack = factory.LazyAttribute(lambda p: "@{}".format(p.slack_temp))

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=FINANCE_GROUP_NAME))
            self.save()


class ApproverFactory(StaffFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(
                GroupFactory(name=STAFF_GROUP_NAME),
                GroupFactory(name=APPROVER_GROUP_NAME),
            )
            self.save()


class ContractingFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(
                GroupFactory(name=CONTRACTING_GROUP_NAME),
            )
            self.save()


class ContractingApproverFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(
                GroupFactory(name=CONTRACTING_GROUP_NAME),
                GroupFactory(name=APPROVER_GROUP_NAME),
            )
            self.save()


class SuperUserFactory(StaffFactory):
    is_superuser = True


class ReviewerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=REVIEWER_GROUP_NAME))
            self.save()


class ApplicantFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=APPLICANT_GROUP_NAME))
            self.save()


class CommunityReviewerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=COMMUNITY_REVIEWER_GROUP_NAME))
            self.save()


class PartnerFactory(UserFactory):
    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if create:
            self.groups.add(GroupFactory(name=PARTNER_GROUP_NAME))
            self.save()
