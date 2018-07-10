import argparse
import json

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError
from django_fsm import FSMField

from opentech.apply.categories.models import Category, Option
from opentech.apply.categories.categories_seed import CATEGORIES
from opentech.apply.funds.models import ApplicationSubmission, FundType, Round, RoundForm
from opentech.apply.funds.workflow import INITIAL_STATE

User = get_user_model()

STREAMFIELD_MAP = {
    "title": {
        "id": "title",
        "type": "direct",
    },
    "field_application_name": {
        "id": "full_name",
        "type": "value",
        # If no Drupal value key is specified, we default to 'value'
        "key": "safe_value",
    },
    "field_application_mail": {
        "id": "email",
        "type": "value",
        "key": "email",
    },
    "field_application_event_date": {
        "id": "date",
        "type": "value",
        "key": "value",
    },
    "field_application_amount": {
        "id": "value",
        "type": "value",
    },
    "field_application_describe": {
        "id": "fe488e12-b5f4-491a-9ca9-d7aff0993884",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_who": {
        "id": "e7a0bc56-ad5d-4be7-9709-eb823a0e6e3d",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_objective_text": {
        "id": "43d52051-27f2-4d30-abf1-173a31f15072",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_strategy": {
        "id": "4e1f46ad-12d7-40c3-a1e8-0793bb327961",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_how": {
        "id": "e33e1415-6832-4ef3-8a10-ae6d3aef61c8",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_collaboration": {
        "id": "812792a3-edc5-4521-b5c7-e9c697122325",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_diverse": {
        "id": "c367cae6-9fde-40fc-8c99-7ca2117bda6a",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_outreach": {
        "id": "14ef1b53-ef85-4756-a13e-19d3c3be7d85",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_needs": {
        "id": "eb6474e1-2f69-4f69-9a9c-edf13c25455c",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_budget": {
        "id": "de631da99f904f5f9c67e3a6e182f7c6",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_cod": {
        "id": "4948cc0fd1d142eeb81dd10784fba0f2",
        "type": "boolean",
    },
    "field_application_otf_mission": {
        "id": "9b20aa6384d54f64b1fb846efed89a41",
        "type": "boolean",
    },
    "field_application_otf_tos": {
        "id": "b4a2f762f61c402aa8d22b58b3201263",
        "type": "boolean",
    },
    "field_application_otf_represent": {
        "id": "9409408f0cee4c97ac0517838eacdd9f",
        "type": "boolean",
    },
    "field_application_otf_license": {
        "id": "e0e6990db8744781afe9d42a105b8ff4",
        "type": "boolean",
    },
    "field_application_otf_complete": {
        "id": "966cd67f04a34c16b4e5892d4cd1e175",
        "type": "boolean",
    },
    "field_application_otf_deadline": {
        "id": "d5b982f829dd4ee4aab3eb5349e6b077",
        "type": "boolean",
    },
    "field_application_otf_list": {
        "id": "4a4feb4e6e5445bd83b42e9f39ca833c",
        "type": "boolean",
    },
    "field_application_otf_newsletter": {
        "id": "e011bd48613648d48263997f71656bfc",
        "type": "boolean",
    },

    "field_concept_upload": {
        "id": "8c4f9cf13d624b64ab70e6cd342921f5",
        "type": "file",
        # TODO: finish mapping
    },
}

FUND = FundType.objects.get(title='Community lab')
ROUND = Round.objects.get(title='Community lab open round')
FORM = RoundForm.objects.get(round=ROUND)

# Monkey patch the status field so it is no longer protected
patched_status_field = FSMField(default=INITIAL_STATE, protected=False)
setattr(ApplicationSubmission, 'status', patched_status_field)


class Command(BaseCommand):
    help = "Community lab migration script. Requires a source JSON file."
    data = []
    terms = {}

    def add_arguments(self, parser):
        parser.add_argument('source', type=argparse.FileType('r'), help='Migration source JSON file')

    @transaction.atomic
    def handle(self, *args, **options):
        # Prepare the list of categories.
        for item in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=item['category'])
            option, _ = Option.objects.get_or_create(value=item['name'], category=category)
            self.terms[item['tid']] = option

        with options['source'] as json_data:
            self.data = json.load(json_data)

            for id in self.data:
                self.process(id)

    def process(self, id):
        node = self.data[id]

        try:
            submission = ApplicationSubmission.objects.get(drupal_id=node['nid'])
        except ApplicationSubmission.DoesNotExist:
            submission = ApplicationSubmission(drupal_id=node['nid'])

        # TODO timezone?
        submission.submit_time = datetime.fromtimestamp(int(node['created']), timezone.utc)
        submission.user = self.get_user(node['uid'])

        submission.page = FUND
        submission.round = ROUND
        submission.form_fields = FORM.form.form_fields

        submission.status = self.get_workflow_state(node)

        form_data = {
            'skip_account_creation_notification': True,
        }

        for field in node:
            if field in STREAMFIELD_MAP:
                try:
                    id = STREAMFIELD_MAP[field]['id']
                    form_data[id] = self.get_field_value(field, node)
                except TypeError:
                    pass

        submission.form_data = form_data

        try:
            submission.save()
            self.stdout.write(f"Processed \"{node['title']}\" ({node['nid']})")
        except IntegrityError:
            pass

    def get_user(self, uid):
        try:
            return User.objects.get(drupal_id=uid)
        finally:
            return None

    def get_field_value(self, field, node):
        """
        Handles the following formats:
        field: {(safe_)value: VALUE}
        field: {target_id: ID} -- Drupal ForeignKey. Reference to other node or user entities.
        field: {tid: ID} -- or term ID. fk to Categories
        field: []
        field: [{value|target_id|tid: VALUE},]
        """
        mapping = STREAMFIELD_MAP[field]
        mapping_type = mapping['type']
        key = mapping.get('key', 'value')
        source_value = node[field]
        value = None

        if mapping_type == "direct":
            value = source_value
        elif mapping_type == 'value':
            value = self.nl2br(source_value[key]) if source_value else ''
        elif mapping_type == 'map' and 'map' in 'mapping':
            value = mapping['map'].get(source_value[key])
        elif mapping_type == 'address' and 'map' in mapping:
            try:
                value_map = mapping['map']
                value = {}
                for item in value_map:
                    value[value_map[item]] = source_value[item]
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

    def get_referenced_term(self, tid):
        try:
            term = self.terms[tid]
            return term.id
        except KeyError:
            return None

    def get_referenced_node(self, nid):
        pass

    def get_workflow_state(self, node):
        """
        workbench_moderation: {'current': {'state': STATE, 'timestamp': TS}}
        """
        states = {
            "draft": "",
            "published": "in_discussion",
            "in_discussion": "in_discussion",
            "council_review": "internal_review",
            "ready_for_reply": "post_review_discussion",
            "contract_review": "post_review_discussion",
            "in_contract": "accepted",
            "invited_for_proposal": "accepted",
            "dropped_concept_note": "rejected",
            "dropped": "rejected",
            "dropped_without_review": "rejected"
        }

        return states.get(node['workbench_moderation']['current']['state'], "in_discussion")

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')
