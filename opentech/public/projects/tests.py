import json

from django.test import TestCase

from opentech.apply.categories.models import Option
from opentech.apply.categories.tests.factories import CategoryFactory, OptionFactory

from .widgets import CategoriesWidget


class TestCategoriesWidget(TestCase):
    def setUp(self):
        self.category = CategoryFactory()
        self.options = OptionFactory.create_batch(3, category=self.category)

    def test_init_has_no_queries(self):
        with self.assertNumQueries(0):
            CategoriesWidget()

    def test_can_access_categories_and_options(self):
        widget = CategoriesWidget()
        widgets = list(widget.widgets)
        self.assertEqual(len(widgets), 1)
        choices = list(widgets[0].choices)
        self.assertEqual(len(choices), len(self.options))
        self.assertCountEqual(list(choices), list(Option.objects.values_list('id', 'value')))

    def test_can_get_multiple_categories(self):
        CategoryFactory()
        widget = CategoriesWidget()
        widgets = list(widget.widgets)
        self.assertEqual(len(widgets), 2)

    def test_can_decompress_data(self):
        widget = CategoriesWidget()
        value = json.dumps({
            self.category.id: [self.options[0].id]
        })
        self.assertEqual(widget.decompress(value), [[self.options[0].id]])

    def test_can_decompress_multiple_data(self):
        new_category = CategoryFactory()
        widget = CategoriesWidget()
        value = json.dumps({
            self.category.id: [self.options[0].id],
            new_category.id: [],
        })
        self.assertEqual(widget.decompress(value), [[self.options[0].id], []])

    def test_can_get_data_from_form(self):
        name = 'categories'
        widget = CategoriesWidget()
        submitted_data = {
            name + '_0': [self.options[1].id],
        }

        value = widget.value_from_datadict(submitted_data, [], name)

        self.assertEqual(value, json.dumps({self.category.id: [self.options[1].id]}))

    def test_can_get_multiple_data_from_form(self):
        new_category = CategoryFactory()
        new_options = OptionFactory.create_batch(3, category=new_category)

        name = 'categories'
        widget = CategoriesWidget()
        answer_1 = [self.options[1].id]
        answer_2 = [new_options[1].id, new_options[2].id]
        submitted_data = {
            name + '_0': answer_1,
            name + '_1': answer_2,
        }

        value = widget.value_from_datadict(submitted_data, [], name)

        self.assertEqual(
            value,
            json.dumps({
                self.category.id: answer_1,
                new_category.id: answer_2,
            })
        )
