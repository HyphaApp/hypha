import argparse
import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "User migration script. Requires a source JSON file."

    def add_arguments(self, parser):
        parser.add_argument('source', nargs='?', type=argparse.FileType('r'), help='Migration source JSON file')
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Perform a run dry-run',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            User = get_user_model()
            users = json.load(json_data)

            from pprint import pprint
            for uid in users:
                user = users[uid]

                full_name = user.get('field_otf_real_name', None)
                if isinstance(name, dict) and 'und' in name:
                    full_name = name['und'][0]['safe_value']

                if not full_name:
                    full_name = user.get('name')

                _, created = User.objects.get_or_create(
                    email=user.get('mail'),
                    defaults={'full_name': full_name}
                )

                if created:
                    print("Imported user %s (%s)" % (uid, full_name))
