from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

import factory


class GroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ('name',)

    name = factory.Sequence('group name {}'.format)


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence('email{}@email.com'.format)

    @factory.PostGeneration
    def groups(self, create, extracted, **kwargs):
        if create:
            if not extracted:
                groups = GroupFactory(**kwargs)
            else:
                groups = extracted

            self.groups.add(groups)
