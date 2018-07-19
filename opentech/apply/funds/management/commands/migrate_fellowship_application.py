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
    "field_application_position": {
        "id": "1282223d-77f5-4047-be03-4df4c4b2148a",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_role": {
        "id": "9c0256e4-42e1-41fe-9880-7f621d6c3458",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_preapplied": {
        "id": "f8efef0a-0632-4c81-b4db-7bc6a06caa7d",
        "type": "map",
        "map": {
            "0": "No",
            "1": "Yes",
        },
    },
    "field_application_describe": {
        "id": "1eb8b4e3-e2bb-4810-a8ce-3fc82a3192c8",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_how": {
        "id": "177d56e8-2df1-4ead-8e3d-4916610fbed6",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_insight": {
        "id": "05ff1755-947b-4e41-8f71-aae99977c572",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_duration2": {
        "id": "611dacd7-553a-4be8-9283-1d006099d0c9",
        "type": "map",
        "map": {
            "3": "3 months",
            "6": "6 months",
            "9": "9 months",
            "12": "12 months",
            "18": "18 months",
        },
    },
    "field_application_host_text": {
        "id": "0afaf4e1-4556-4e79-aa3d-4990e33620da",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_host2_text": {
        "id": "a543b34f-ae6a-4b17-8ac3-ececc14573a0",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_questions": {
        "id": "57cc52e2-b3ff-4e9f-a5fe-42e7735e16c2",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_status": {
        "id": "ff4d12ff-7b88-4e87-bb5b-81543aef0e25",
        "type": "category",
        "key": "tid",
    },
    "field_application_objectives": {
        "id": "30c41288-a762-4003-acce-8c12e7343d90",
        "type": "category",
        "key": "tid",
    },
    "field_application_beneficiaries": {
        "id": "56833441-542b-4a06-8ad2-8e7e8fd1a334",
        "type": "category",
        "key": "tid",
    },
    "field_application_focus": {
        "id": "6b404851-ce2b-494f-b9f7-62858a937469",
        "type": "category",
        "key": "tid",
    },
    "field_application_problems": {
        "id": "590e4b77-c4f4-4bd0-b5be-2ad2851da4f5",
        "type": "category",
        "key": "tid",
    },
    "field_term_region": {
        "id": "81c01278-8ba4-4d84-a1da-e05a07aad874",
        "type": "category",
        "key": "tid",
    },
    "field_concept_upload": {
        "id": "25740b9d-0f8f-4ce1-88fa-c6ee831c6aef",
        "type": "file",
        # TODO: finish mapping
    },
    "field_application_otf_mission": {
        "id": "5178e15f-d442-4d36-824d-a4292ef77062",
        "type": "boolean",
    },
    "field_application_otf_tos": {
        "id": "bd91e220-4cdb-4392-8054-7b7dfe667d46",
        "type": "boolean",
    },
    "field_application_otf_represent": {
        "id": "8d000129-ca8b-48cf-8dc2-4651bcbe46e8",
        "type": "boolean",
    },
    "field_application_otf_license": {
        "id": "92f0801e-b9dc-4edc-9716-3f1709ae1c9b",
        "type": "boolean",
    },
    "field_application_otf_complete": {
        "id": "3a3f2da3-4e32-4b86-9060-29c606927114",
        "type": "boolean",
    },
    "field_application_otf_deadline": {
        "id": "19395179-ed9f-4556-9b6b-ab5caef4f610",
        "type": "boolean",
    },
    "field_application_otf_list": {
        "id": "1345a8eb-4dcc-4170-a5ac-edda42d4dafc",
        "type": "boolean",
    },
    "field_application_otf_newsletter": {
        "id": "4ca22ebb-daba-4fb6-a4a6-b130dc6311a8",
        "type": "boolean",
    },
}

FUND = FundType.objects.get(title='Fellowship archive fund')
ROUND = Round.objects.get(title='Fellowship archive round')
FORM = RoundForm.objects.filter(round=ROUND)[0]

# Monkey patch the status field so it is no longer protected
patched_status_field = FSMField(default=INITIAL_STATE, protected=False)
setattr(ApplicationSubmission, 'status', patched_status_field)


class Command(BaseCommand):
    help = "Fellowship application migration script. Requires a source JSON file."
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

        if "value" not in form_data:
            form_data["value"] = 0

        submission.form_data = form_data

        try:
            submission.save()
            self.stdout.write(f"Processed \"{node['title']}\" ({node['nid']})")
        except IntegrityError:
            self.stdout.write(f"Skipped \"{node['title']}\" ({node['nid']}) due to IntegrityError")
            pass

    def get_user(self, uid):
        try:
            return User.objects.get(drupal_id=uid)
        except User.DoesNotExist:
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
            "council_review": "concept_internal_review",
            "ready_for_reply": "concept_review_discussion",
            "contract_review": "concept_review_discussion",
            "in_contract": "invited_to_proposal",
            "invited_for_proposal": "invited_to_proposal",
            "dropped_concept_note": "concept_rejected",
            "dropped": "concept_rejected",
            "dropped_without_review": "concept_rejected"
        }

        return states.get(node['workbench_moderation']['current']['state'], "in_discussion")

    def nl2br(self, value):
        return value.replace('\r\n', '<br>\n')
