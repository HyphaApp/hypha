import argparse
import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.users.groups import STAFF_GROUP_NAME


class Command(BaseCommand):
    help = "User migration script. Requires a source JSON file."
    groups = Group.objects.all()

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            User = get_user_model()
            users = json.load(json_data)

            for uid in users:
                user = users[uid]

                full_name = self.get_full_name(user)
                user_object, created = User.objects.get_or_create(
                    email=user.get('mail'),
                    defaults={
                        'full_name': full_name,
                        'drupal_id': uid,
                    }
                )

                operation = "Imported" if created else "Processed"

                groups = self.get_user_groups(user)
                user_object.groups.set(groups)

                # Ensure uid is set
                user_object.drupal_id = uid
                user_object.save()

                self.stdout.write(f"{operation} user {uid} ({full_name})")

    def get_full_name(self, user):
        full_name = user.get('field_otf_real_name', None)
        try:
            """
            Drupal is i18n-ready out of the box. As such, the data
            structure includes a language reference, defaulting to 'und' (undefined)
            In addition to that, most fields are arrays indexed by language, and
            the value delta. Different field types will have a different value.
            Native entity fields are loaded directly (as string or int). They are
            things like entity id, owner, created/updated timestamp.
            And name/mail on users.
            """
            full_name = full_name['und'][0]['safe_value']
        except (KeyError, TypeError):
            full_name = user.get('name')

        return full_name

    def get_user_groups(self, user):
        groups = []
        role_map = {
            'proposer': 'Applicant',
            'council': 'Advisor',
            'administrator': 'Administrator',
            'dev': 'Administrator',
        }

        _, email_domain = user.get('mail').split('@')
        if email_domain in settings.STAFF_EMAIL_DOMAINS:
            groups.append(self.groups.filter(name=STAFF_GROUP_NAME).first())

        roles = [role for role in user.get('roles').values() if role != "authenticated user"]

        for role in roles:
            group_name = role_map.get(role)
            if group_name:
                groups.append(self.groups.filter(name=group_name).first())

        return groups
