from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "1. Mark all accounts that has not logged in after 5 month after creation as inactive."

    @transaction.atomic
    def handle(self, *args, **options):
        onehundredfifty_days_ago = timezone.now() - timedelta(days=150)
        User = get_user_model()
        users_inactivate = User.objects.filter(date_joined__date__lte=onehundredfifty_days_ago, is_active=True, is_staff=False, last_login__isnull=True)

        for user in users_inactivate:
            user.is_active = False
            user.save()

        # TODO 2. Delete accounts that has never logged in and has no applications.
        # As it is now might delete accounts that should remain.
        # users_delete = User.objects.filter(date_joined__date__lte=onehundredfifty_days_ago, is_active=False, is_staff=False, last_login__isnull=True, groups__isnull=True, applicationsubmission__isnull=True).order_by('pk')

        # for user in users_delete:
        #     # user.delete()
        #     print(f'Delete {user}:{user.pk}')

        # delete_count = users_delete.count()
        # print(f'Delete {delete_count} users')
