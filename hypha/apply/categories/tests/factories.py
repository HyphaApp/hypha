import factory

from ..models import Category, Option


class CategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    help_text = factory.Faker('sentence')


class OptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Option

    value = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)
