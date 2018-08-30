import argparse
import json

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from opentech.apply.determinations.models import Determination
from opentech.apply.funds.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Determination migration script. Requires a source JSON file."
    data = []

    STREAMFIELD_MAP = {
        "field_cnr_technical": {
            "id": "technical",
            "type": "value",
            "key": "safe_value",
        },
        "field_cnr_principles": {
            "id": "principles",
            "type": "value",
            "key": "safe_value",
        },
        "field_cnr_sustainable": {
            "id": "sustainable",
            "type": "value",
            "key": "safe_value",
        },
        "field_cnr_comments": {
            "id": "comments",
            "type": "value",
            "key": "safe_value",
        },
        "field_cnsr_determination_message": {
            "id": "message",
            "type": "value",
            "key": "safe_value",
        },
    }

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        with options['source'] as json_data:
            self.data = json.load(json_data)

            blacklist = {"8104"}

            for id in self.data:
                if id not in blacklist:
                    self.process(id)

    def process(self, id):
        node = self.data[id]
        form_data = {}

        try:
            determination = Determination.objects.get(drupal_id=node['nid'])
        except Determination.DoesNotExist:
            determination = Determination(drupal_id=node['nid'])

        # TODO timezone?
        determination.created_at = datetime.fromtimestamp(int(node['created']), timezone.utc)
        determination.updated_at = datetime.fromtimestamp(int(node['changed']), timezone.utc)
        determination.author = self.get_user(node['uid'])
        determination.submission = self.get_submission(node)
        determination.outcome = self.get_determination(node)
        determination.message = self.get_field_value('field_cnsr_determination_message', node)

        for field in node:
            if field in self.STREAMFIELD_MAP:
                try:
                    id = self.STREAMFIELD_MAP[field]['id']
                    if id != 'message':
                        form_data[id] = self.get_field_value(field, node)
                except TypeError:
                    pass

        determination.data = form_data

        try:
            determination.save()
            self.stdout.write(f"Processed \"{node['title']}\" ({node['nid']})")
        except IntegrityError:
            self.stdout.write(f"Skipped \"{node['title']}\" ({node['nid']}) due to IntegrityError")
            pass

    def get_field_value(self, field, node):
        """
        Handles the following formats:
        field: {(safe_)value: VALUE}
        field: {target_id: ID} -- Drupal ForeignKey. Reference to other node or user entities.
        field: {tid: ID} -- or term ID. fk to Categories
        field: []
        field: [{value|target_id|tid: VALUE},]
        """
        mapping = self.STREAMFIELD_MAP[field]
        mapping_type = mapping['type']
        key = mapping.get('key', 'value')
        source_value = node[field]
        value = None

        if mapping_type == "direct":
            value = source_value
        elif mapping_type == 'value':
            if key in source_value:
                value = self.nl2br(source_value[key]) if source_value else ''
            else:
                value = self.nl2br(source_value['value']) if source_value else ''
        elif mapping_type == 'map' and 'map' in 'mapping':
            value = mapping['map'].get(source_value[key])
        elif mapping_type == 'address' and 'map' in mapping:
            try:
                value_map = mapping['map']
                value = {}
                for item in value_map:
                    value[value_map[item]] = source_value[item]
                value = json.dumps(value)
            except TypeError:
                value = {}
        elif mapping_type == 'boolean':
            value = source_value[key] == '1' if source_value else False
        elif mapping_type == 'category':
            if not source_value:
                value = []
            else:
                if isinstance(source_value, dict):
                    option = self.get_referenced_term(source_value[key])
                    value = [option] if option else []
                else:
                    value = []
                    for item in source_value:
                        option = self.get_referenced_term(item[key])
                        if option:
                            value.append(option)
        elif mapping_type == 'file':
            # TODO finish mapping. Requires access to the files.
            value = {}

        return value

    def get_user(self, uid):
        try:
            User = get_user_model()
            return User.objects.get(drupal_id=uid)
        except User.DoesNotExist:
            return None

    def get_submission(self, node):
        try:
            nid = node['field_submission_concept_note']['target_id']
            return ApplicationSubmission.objects.get(drupal_id=nid)
        except ApplicationSubmission.DoesNotExist:
            return 'None'

    def get_determination(self, node):
        choices = {
            "invited": 2,
            "approved": 2,
            "dropped": 0,
            "unapproved": 0,
            "undetermined": 1
        }

        try:
            determination = choices.get(node['field_cnsr_determination']['value'], 1)
        except TypeError:
            determination = 1

        return determination

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')
