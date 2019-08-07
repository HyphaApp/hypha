import factory

from opentech.apply.funds.tests.factories import ApplicationSubmissionFactory
from opentech.apply.projects.models import Project


class ProjectFactory(factory.DjangoModelFactory):
    submission = factory.SubFactory(ApplicationSubmissionFactory)

    name = factory.Sequence('name {}'.format)

    class Meta:
        model = Project
