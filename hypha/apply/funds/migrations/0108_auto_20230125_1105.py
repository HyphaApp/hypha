# Generated by Django 3.2.16 on 2023-01-25 11:05

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('funds', '0107_add_additional_fields_to_funds_labs'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationsubmission',
            name='search_document',
            field=django.contrib.postgres.search.SearchVectorField(null=True),
        ),
        migrations.AddIndex(
            model_name='applicationsubmission',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_document'], name='funds_appli_search__43a072_gin'),
        ),
    ]
