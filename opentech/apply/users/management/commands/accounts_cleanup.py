from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "1. Mark all accounts that has not logged in after 3 month after creation as inactive. 2. Delete accounts that has never logged in and has no applications"

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.filter(last_login__isnull=True, groups__isnull=True, applicationsubmission__isnull=True)
        for user in users:
            user.is_active = False
            user.save()
