import argparse
import json

from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from opentech.apply.categories.models import Category, Option
from opentech.apply.categories.categories_seed import CATEGORIES
from opentech.apply.funds.models import ApplicationSubmission, FundType, Round

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
    "field_application_preapplied": {
        "id": "49a0f5f4-e8e9-4dfc-8575-205ee9675032",
        "type": "map",
        "map": {
            "0": "No",
            "1": "Yes",
        },
    },
    "field_application_apply_for": {
        "id": "c1277029-1718-40e3-8bf5-d80ece7fd343",
        "type": "map",
        "map": {
            "direct": "Direct funding",
            "receive": "Requesting to receive services",
            "provide": "Requesting to provide services",
        },
    },
    "field_application_amount": {
        "id": "value",
        "type": "value",
    },
    "field_application_amount_text": {
        "id": "value",
        "type": "value",
    },
    "field_application_service": {
        "id": "ebdf9a22-58c7-4bd6-a58d-e71363357470",
        "type": "map",
        "map": {
            "audit": "Audit of presumably compromised websites",
            "ddos": "DDoS response and mitigation",
            "hosting": "Secure web hosting",
            "hostingevents": "Secure hosting for monitoring and resiliency of websites during special events (elections, campaigns etc.)",
            "vpn": "VPN connections",
            "isp": "Safe internet connections",
            "analysis": "Forensic analysis of digital attacks",
            "recovery": "Recovery of compromised websites",
            "malware": "Malware analysis",
            "equipment": "Equipment replacements (unavailable)",
            "legalhelp": "Finding legal representation (unavailable)",
            "legalfees": "Payment of legal fees (unavailable)",
        },
    },
    "field_application_service_other": {
        "id": "c8c329c7-78e4-4cbf-a3b1-77a1324e92ff",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_duration3": {
        "id": "806d401c-b52c-46f7-9e96-f36fa70f53d8",
        "type": "map",
        "map": {
            "1": "1 month",
            "2": "2 months",
            "3": "3 months",
            "4": "4 months",
            "5": "5 months",
            "6": "6 months",
        },
    },
    "field_application_who": {
        "id": "1ec16cdc-7a68-40be-b17b-9a218def4260",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_how": {
        "id": "4fa2ac11-d1cd-4d23-8082-93a14c8f99c8",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_sustainability": {
        "id": "3cde39ae-b687-4c4f-b58b-849396c2fdb8",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_dates": {
        "id": "0b2a4653-b390-44a6-b92e-fae4647e7ec4",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_why": {
        "id": "6d75e412-cf53-4833-9f1d-3e0126512fb9",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_why_rapiid": {
        "id": "1b181d1e-ef91-41af-b9c1-d096a991314b",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_focus": {
        "id": "efd91eaf-378f-4aab-96cb-c5601155cbee",
        "type": "category",
        "key": "tid",
    },
    "field_application_objectives": {
        "id": "4be0c7bd-231d-4d9f-bd47-8589fc005f54",
        "type": "category",
        "key": "tid",
    },
    "field_application_beneficiaries": {
        "id": "6e0293ee-218e-4c3b-b82d-5bf91fdb21c9",
        "type": "category",
        "key": "tid",
    },
    "field_term_region": {
        "id": "6ff029c6-c6d1-4c37-a49a-46181b1cd33d",
        "type": "category",
        "key": "tid",
    },
    "field_application_problems": {
        "id": "7fb1001e-d458-414f-a5bb-006db6f89baf",
        "type": "category",
        "key": "tid",
    },
    "field_application_budget": {
        "id": "45d7d38a-9c9d-4c43-98df-bb95d4a1dd77",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_legal_name": {
        "id": "632065c5-860f-4751-9b31-52914d7c6448",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_contact": {
        "id": "13bb0d64-65f3-4340-8e7e-e5da80d706d5",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_phone": {
        "id": "2cb9fe4b-df45-4181-80e5-14382f853081",
        "type": "value",
        "key": "safe_value",
    },
    "field_application_address": {
        "id": "bd29eb88-9754-4305-9b2d-406a875ec56a",
        "type": "address",
        "map": {
            "administrative_area": "administrative_area",
            "country": "country",
            "locality": "locality_name",
            "postal_code": "postal_code",
            "thoroughfare": "thoroughfare",
            "premise": "premise",
        }
    },
    "field_application_otf_mission": {
        "id": "e695f0d7-4c74-4cc6-853f-bd62ecd19d3d",
        "type": "boolean",
    },
    "field_application_otf_tos": {
        "id": "f40d1acc-d802-4cc6-b0e9-fff78dc54223",
        "type": "boolean",
    },
    "field_application_otf_represent": {
        "id": "0b3c0827-38e2-439b-bca5-735835af1019",
        "type": "boolean",
    },
    "field_application_otf_license": {
        "id": "bc9c960e-a6f4-4bc2-b626-efb5bc5552c6",
        "type": "boolean",
    },
    "field_application_otf_complete": {
        "id": "5812b66d-630e-4ca2-8bea-819084278f55",
        "type": "boolean",
    },
    "field_application_otf_deadline": {
        "id": "97d3746c-cf0f-449a-b3a3-7a9cdd45cc6d",
        "type": "boolean",
    },
    "field_application_otf_list": {
        "id": "fc3d2a87-1151-418b-b1cd-9289f00bde35",
        "type": "boolean",
    },
    "field_application_otf_newsletter": {
        "id": "83ecc69a-f47c-495e-bc8f-326e55aed67a",
        "type": "boolean",
    },
    # TODO
    # "field_concept_upload": {
    #     "id": "607daeba-1f33-4ad0-b135-eda743ba8e3a",
    #     "type": "file",
    # },
}

FUND = FundType.objects.get(title='Rapid Response')
ROUND = Round.objects.get(title='Rapid Response open round')


class Command(BaseCommand):
    help = "Rapid response migration script. Requires a source JSON file."
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
                return

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
        form_data = {}

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
            value = source_value[key] if source_value else ''
        elif mapping_type == 'map' and 'map' in 'mapping':
            value = mapping['map'].get(source_value[key])
        elif mapping_type == 'address' and 'map' in mapping:
            try:
                value_map = mapping['map']
                value = {}
                for item in value_map:
                    value[value_map['item']] = source_value[item]
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
                    value = [self.get_referenced_term(item[key]) for item in source_value]

        return value

    def get_referenced_term(self, tid):
        try:
            term = self.terms[tid]
            return term.id
        finally:
            return None

    def get_referenced_node(self, nid):
        pass

    def get_workflow_state(self):
        """
        workbench_moderation: {'current': {'state': STATE, 'timestamp': TS}}
        """
        pass
