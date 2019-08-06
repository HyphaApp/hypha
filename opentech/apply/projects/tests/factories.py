import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.projects.models import Project
from opentech.apply.users.tests.factories import UserFactory


class ProjectFactory(factory.DjangoModelFactory):
    submission = factory.SubFactory(ApplicationSubmissionFactory)

    title = factory.Sequence('name {}'.format)
    user = factory.SubFactory(UserFactory)

    class Meta:
        model = Project
