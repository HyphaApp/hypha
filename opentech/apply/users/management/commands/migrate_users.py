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
                slack_name = self.get_slack_name(user)
                user_object, created = User.objects.get_or_create(
                    email=self.get_email(user, options['anonymize']),
                    defaults={
                        'full_name': full_name,
                        'slack': slack_name,
                        'drupal_id': uid,
                    }
                )

                operation = "Imported" if created else "Processed"

                groups = self.get_user_groups(user)
                user_object.groups.set(groups)

                # Allow for updating the slack user name.
                if not created:
                    user_object.slack = slack_name

                # Set random password on new accounts.
                if created:
                    password = User.objects.make_random_password(length=16)
                    user_object.set_password(password)

                # Ensure uid is set
                user_object.drupal_id = uid
                user_object.save()

                self.stdout.write(f"{operation} user {uid} ({full_name})")

    def get_full_name(self, user):
        full_name = user.get('field_otf_real_name', None)
        try:
            full_name = full_name['safe_value']
        except (KeyError, TypeError):
            full_name = user['name']

        return full_name

    def get_slack_name(self, user):
        slack_name = user.get('field_otf_slack_name', None)
        try:
            slack_name = f"@{slack_name['safe_value']}"
        except (KeyError, TypeError):
            slack_name = ''

        return slack_name

    def get_user_groups(self, user):
        groups = []
        role_map = {
            'council': 'Reviewer',
        }

        if self.is_staff(user['mail']):
            groups.append(self.groups.filter(name=STAFF_GROUP_NAME).first())

        roles = [role for role in user.get('roles').values() if role != "authenticated user"]

        for role in roles:
            group_name = role_map.get(role)
            if group_name:
                groups.append(self.groups.filter(name=group_name).first())

        return groups

    def get_email(self, user, anonymize=False):
        email = user['mail']
        if not anonymize or self.is_staff(email):
            return email

        return f"aeon+{user['uid']}@torchbox.com"

    def is_staff(self, email):
        _, email_domain = email.split('@')
        return email_domain in settings.STAFF_EMAIL_DOMAINS
