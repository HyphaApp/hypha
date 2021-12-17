# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model('contenttypes.ContentType')
    Page = apps.get_model('wagtailcore.Page')
    Site = apps.get_model('wagtailcore.Site')
    ApplyHomePage = apps.get_model('apply_home.ApplyHomePage')

    # Create content type for homepage model
    homepage_content_type, created = ContentType.objects.get_or_create(
        model='applyhomepage', app_label='apply_home')

    # Create a new homepage
    applyhomepage = ApplyHomePage.objects.create(
        title="Apply Homepage",
        draft_title="Apply Homepage",
        slug='apply',
        content_type=homepage_content_type,
        path='00010002',
        depth=2,
        numchild=0,
        url_path='/apply/',
    )

    # Create a site with the new homepage set as the root
    Site.objects.create(
        hostname='apply.localhost', root_page=applyhomepage, is_default_site=False)


class Migration(migrations.Migration):

    run_before = [
        ('wagtailcore', '0053_locale_model'),  # added for Wagtail 2.11 compatibility
    ]

    dependencies = [
        ('funds', '0001_initial'),
        ('apply_home', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_homepage),
    ]
