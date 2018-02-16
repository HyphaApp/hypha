from django.contrib.auth import get_user_model

import factory


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence('email{}@email.com'.format)
