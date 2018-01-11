import factory

from ..models import Category


class CategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    help_text = factory.Faker('sentence')
