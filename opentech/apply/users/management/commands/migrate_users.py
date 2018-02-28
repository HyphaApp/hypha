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
        parser.add_argument('source', nargs='?', type=argparse.FileType('r'), help='Migration source JSON file')

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

                for group in self.get_user_groups(user):
                    user_object.groups.add(group)

                # Ensure uid is set
                user_object.drupal_id = uid
                user_object.save()

                print(f"{operation} user {uid} ({full_name})")

    def get_full_name(self, user):
        full_name = user.get('field_otf_real_name', None)
        try:
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
