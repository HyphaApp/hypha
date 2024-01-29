import click
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.models import Site


class Command(BaseCommand):
    help = (
        "Run this to initialize this project. Set a superuser and wagtail sites domain."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        click.echo(
            "Provide the details below to initialize Hypha. Press enter to keep the default value.\n"
        )

        APPLY_SITE_DOMAIN = click.prompt("Site Domain", default="hypha.test")
        SUPER_ADMIN_EMAIL = click.prompt(
            "Superadmin Email ", default="superadmin@hypha.test"
        )
        SUPER_ADMIN_PASSWORD = click.prompt("Superadmin Password ", default="hypha123")
        SITE_PORT = click.prompt("Site port", default="9001")

        User = get_user_model()

        # Create Superuser
        try:
            user = User.objects.get(email=SUPER_ADMIN_EMAIL)
            user.set_password(SUPER_ADMIN_PASSWORD)
        except User.DoesNotExist:
            User.objects.create_superuser(
                email=SUPER_ADMIN_EMAIL, password=SUPER_ADMIN_PASSWORD
            )
        click.secho(
            f">>> Created superuser with email {SUPER_ADMIN_EMAIL}.", fg="green"
        )

        # Set site port and domain
        click.secho(
            f">>> Set apply site to {APPLY_SITE_DOMAIN}:{SITE_PORT}", fg="green"
        )
        site_apply = Site.objects.get(id=2)
        site_apply.hostname = APPLY_SITE_DOMAIN
        site_apply.port = SITE_PORT
        site_apply.save()
