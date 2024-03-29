# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-15 13:15
from __future__ import unicode_literals

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

from hypha.apply.users.groups import GROUPS


def add_groups(apps, schema_editor):
    # Workaround for https://code.djangoproject.com/ticket/23422
    db_alias = schema_editor.connection.alias
    emit_post_migrate_signal(2, False, db_alias)

    Group = apps.get_model("auth.Group")
    Permission = apps.get_model("auth.Permission")

    for group_data in GROUPS:
        group, created = Group.objects.get_or_create(name=group_data["name"])
        for permission in group_data["permissions"]:
            try:
                group.permissions.add(Permission.objects.get(codename=permission))
            except ObjectDoesNotExist:
                print("Could not find the '%s' permission" % permission)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth.Group")

    groups = [group_data["name"] for group_data in GROUPS]
    Group.objects.filter(name__in=groups).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("wagtailadmin", "0001_create_admin_access_permissions"),
        ("wagtailimages", "0002_initial_data"),
        ("wagtaildocs", "0002_initial_data"),
        ("contenttypes", "__latest__"),
    ]

    operations = [migrations.RunPython(add_groups, remove_groups)]
