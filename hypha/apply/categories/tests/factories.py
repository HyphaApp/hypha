import factory

from ..models import Category, Option


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        skip_postgeneration_save = True

    name = factory.Faker("word")
    help_text = factory.Faker("sentence")


class OptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Option
        skip_postgeneration_save = True

    value = factory.Faker("word")
    category = factory.SubFactory(CategoryFactory)
