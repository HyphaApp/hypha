# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_homepage(apps, schema_editor):
    # Get models
    ContentType = apps.get_model('contenttypes.ContentType')
    Page = apps.get_model('wagtailcore.Page')
    Site = apps.get_model('wagtailcore.Site')
    ApplyHomePage = apps.get_model('apply.ApplyHomePage')

    # Create content type for homepage model
    homepage_content_type, created = ContentType.objects.get_or_create(
        model='applyhomepage', app_label='apply')

    # Create a new homepage
    applyhomepage = ApplyHomePage.objects.create(
        title="ApplyHomepage",
        draft_title="ApplyHomepage",
        slug='apply',
        content_type=homepage_content_type,
        path='00010002',
        depth=2,
        numchild=0,
        url_path='/apply/',
    )

    # Create a site with the new homepage set as the root
    Site.objects.create(
        hostname='apply.localhost', root_page=applyhomepage, is_default_site=True)


class Migration(migrations.Migration):

    dependencies = [
        ('apply', '0001_initial'),
        ('home', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_homepage),
    ]
