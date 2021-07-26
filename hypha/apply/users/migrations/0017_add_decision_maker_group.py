from django.core.exceptions import ObjectDoesNotExist
from django.core.management.sql import emit_post_migrate_signal
from django.db import migrations

from hypha.apply.users.groups import DECISION_MAKER_GROUP_NAME, GROUPS


def add_groups(apps, schema_editor):
    # Workaround for https://code.djangoproject.com/ticket/23422
    db_alias = schema_editor.connection.alias
    emit_post_migrate_signal(2, False, db_alias)

    Group = apps.get_model('auth.Group')
    Permission = apps.get_model('auth.Permission')

    for group_data in GROUPS:
        group, created = Group.objects.get_or_create(name=group_data['name'])
        for codename in group_data['permissions']:
            try:
                permission = Permission.objects.get(codename=codename)
            except ObjectDoesNotExist:
                print(f"Could not find the '{permission}' permission")
                continue

            group.permissions.add(permission)


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth.Group')
    Group.objects.filter(name=DECISION_MAKER_GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_add_finance_group'),
    ]

    operations = [
        migrations.RunPython(add_groups, remove_groups)
    ]
