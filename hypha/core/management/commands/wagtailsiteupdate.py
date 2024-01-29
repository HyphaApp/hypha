from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Site


class Command(BaseCommand):
    help = "Wagtail site update script. Requires a public hostname, a apply hostname and a port number in that order."

    def add_arguments(self, parser):
        parser.add_argument("apply", type=str, help="Hostname for the apply site.")
        parser.add_argument("port", type=int, help="Port to use for all sites.")

    @transaction.atomic
    def handle(self, *args, **options):
        site_apply = Site.objects.get(id=2)
        site_apply.hostname = options["apply"]
        site_apply.port = options["port"]
        site_apply.save()

        self.stdout.write(
            f"Updated the apply site to {options['apply']}:{options['port']}."
        )
