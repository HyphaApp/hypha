# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from opentech.apply.categories.categories_seed import CATEGORIES

def prepopulate_categories(apps, schema_editor):
    Category = apps.get_model('categories.Category')
    Option = apps.get_model('categories.Option')


    for item in CATEGORIES:
        category, _ = Category.objects.get_or_create(name=item['category'])
        term, _ = Option.objects.get_or_create(value=item['name'], category=category)

def clean_prepopulated_categories(apps, schema_editor):
    Category = apps.get_model('categories.Category')

    categories = [item['category'] for item in CATEGORIES]
    Category.objects.filter(name__in=categories).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0001_initial')
    ]

    operations = [
        migrations.RunPython(prepopulate_categories, clean_prepopulated_categories)
    ]
