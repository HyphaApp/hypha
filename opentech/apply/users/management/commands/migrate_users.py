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
        parser.add_argument('source', type=argparse.FileType('r'), help="Migration source JSON file")
        parser.add_argument('--anonymize', action='store_true', help="Anonymizes non-OTF emails")

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            User = get_user_model()
            users = json.load(json_data)

            for uid in users:
                user = users[uid]

                full_name = self.get_full_name(user)
                user_object, created = User.objects.get_or_create(
                    email=self.get_email(user, options['anonymize']),
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
            # The Drupal data structure includes a language reference.
            # The default is 'und' (undefined).
            full_name = full_name['und'][0]['safe_value']
        except (KeyError, TypeError):
            full_name = user['name']

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

    def get_email(self, user, anonymize=False):
        if not anonymize:
            return user['mail']

        _, email_domain = user['mail'].split('@')
        if email_domain in settings.STAFF_EMAIL_DOMAINS:
            return user['mail']

        return "aeon+%s@torchbox.com" % user['uid']
