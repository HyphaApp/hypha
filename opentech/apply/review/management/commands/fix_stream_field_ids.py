import json
import uuid

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Fix stream fields so all have unique IDs."

    @transaction.atomic
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, form_fields FROM review_reviewform')
            form_fields = cursor.fetchall()

        for row in form_fields:
            review_id, review_form = row
            form = json.loads(review_form)
            updated = False
            for field in form:
                if field['id'] == '976386e1-3a66-490f-9e82-bfbe1f134cf2':
                    field['id'] = str(uuid.uuid4())
                    updated = True

            if updated:
                updated_form = json.dumps(form)
                with connection.cursor() as cursor:
                    cursor.execute('UPDATE review_reviewform SET form_fields = %s WHERE id = %s', [updated_form, review_id])
