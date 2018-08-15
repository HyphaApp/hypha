import argparse
import json

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from opentech.apply.activity.models import Activity
from opentech.apply.funds.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Comment migration script. Requires a source JSON file."
    data = []

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            self.data = json.load(json_data)

            for id in self.data:
                self.process(id)

    def process(self, id):
        comment = self.data[id]

        activity = Activity.objects.create(
            timestamp=datetime.fromtimestamp(int(comment['created']), timezone.utc),
            user=self.get_user(comment['uid']),
            submission=self.get_submission(comment['nid']),
            message=self.get_message(comment['subject'], comment['comment_body']['safe_value']),
        )

        try:
            activity.save()
            self.stdout.write(f"Processed \"{comment['subject']}\" ({comment['cid']})")
        except IntegrityError:
            self.stdout.write(f"Skipped \"{comment['subject']}\" ({comment['cid']}) due to IntegrityError")
            pass

    def get_user(self, uid):
        try:
            User = get_user_model()
            return User.objects.get(drupal_id=uid)
        except User.DoesNotExist:
            return None

    def get_message(self, comment_subject, comment_body):
        message = f"<p>{comment_subject}</p>{comment_body}"
        return self.nl2br(message)

    def get_submission(self, nid):
        try:
            return ApplicationSubmission.objects.get(drupal_id=nid)
        except ApplicationSubmission.DoesNotExist:
            return 'None'

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')
