from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.core.models import Site


class Command(BaseCommand):
    help = "Wagtail site update script. Requires a public hostname, a apply hostname and a port number in that order."

    def add_arguments(self, parser):
        parser.add_argument('public', type=str, help='Hostname for the public site.')
        parser.add_argument('apply', type=str, help='Hostname for the apply site.')
        parser.add_argument('port', type=int, help='Port to use for all sites.')

    @transaction.atomic
    def handle(self, *args, **options):
        site_apply = Site.objects.get(id=2)
        site_apply.hostname = options['apply']
        site_apply.port = options['port']
        site_apply.save()

        site_public = Site.objects.get(id=3)
        site_public.hostname = options['public']
        site_public.port = options['port']
        site_public.save()

        self.stdout.write(f"Updated the public site to {options['public']}:{options['port']} and the apply site to {options['apply']}:{options['port']}.")
