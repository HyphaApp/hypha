import argparse
import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "User migration script. Requires a source JSON file."

    def add_arguments(self, parser):
        parser.add_argument('source', nargs='?', type=argparse.FileType('r'))
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Perform a run dry-run',
        )

    def handle(self, *args, **options):
        with options['source'] as json_data:
            User = get_user_model()
            users = json.load(json_data)

            for user in users:
                full_name = user.get('field_otf_real_name', None)
                if not full_name:
                    full_name = user.get('name')

                _, created = User.objects.get_or_create(
                    email=user.get('mail'),
                    defaults={'full_name': full_name}
                )

                if created:
                    print("Imported user %s (%s)" % (user['uid'], full_name))
