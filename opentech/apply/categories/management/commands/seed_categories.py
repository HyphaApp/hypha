from django.core.management.base import BaseCommand
from django.db import transaction

from opentech.apply.categories.models import Category, Option
from opentech.apply.categories.categories_seed import CATEGORIES


class Command(BaseCommand):
    help = "Pre-seeds the global application categories. Application Forms and Fund Types seeding depend on this."

    @transaction.atomic
    def handle(self, *args, **options):
        for item in CATEGORIES:
            category, created = Category.objects.get_or_create(name=item['category'])
            if created:
                self.stdout.write(self.style.SUCCESS(f"Category {item['category']} created"))
            term, created = Option.objects.get_or_create(value=item['name'], category=category)
            if created:
                self.stdout.write(f"Term {item['name']} added to category {item['category']}")
