from opentech.apply.funds.management.commands.migration_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Internet Freedom Fund"
    ROUND_NAME = "Internet Freedom Fund"
    APPLICATION_TYPE = "proposal"

    STREAMFIELD_MAP = {
        "title": {
            "id": "title",
            "type": "direct",
        },
        "field_proposal_funding": {
            "id": "value",
            "type": "value",
        },
        "field_proposal_term_time": {
            "id": "duration",
            "type": "value",
        },
        "field_proposal_legal_entity_name": {
            "id": "739a413b-46cc-4936-82ce-e68c2dfa41ca",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_common_name": {
            "id": "full_name",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_entity_contact": {
            "id": "a3c9af86-d047-4663-864a-b6dd97a60c39",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_entity_mail": {
            "id": "email",
            "type": "value",
            "key": "email",
        },
        "field_proposal_entity_phone": {
            "id": "40479d2a-7d53-4c81-834a-775ccd6c91c0",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_entity_address": {
            "id": "f7e431b1-9965-4ebe-ab30-a00ff4b972ec",
            "type": "address",
            "map": {
                "administrative_area": "administrativearea",
                "country": "country",
                "locality": "localityname",
                "postal_code": "postalcode",
                "thoroughfare": "thoroughfare",
                "premise": "premise",
            }
        },
        "field_proposal_summary": {
            "id": "a7502e97-5f2e-417f-b08c-588d367e40e5",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_narrative": {
            "id": "072f181b-90a2-4bb2-986d-55e1aaa9f348",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_objectives": {
            "id": "a7ae7375-4569-47e2-8ee7-3c3d441375a9",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_activities": {
            "id": "50328cc9-879d-4817-8454-2062ac47aef9",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_budget_details": {
            "id": "7b0b0af4-009f-45db-b20c-5f991bce7752",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_similar_efforts": {
            "id": "ba3733f3-bee8-4fe8-bdde-36812aa4df77",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_evaluation": {
            "id": "23028eab-92c3-4c30-9a3e-5604dec0854d",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_sustainability": {
            "id": "88d635e4-81d6-413c-8e09-52b74015e78b",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_fund_info": {
            "id": "38072bb7-fcdd-4f74-9bfb-db45bfeb07a7",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_background": {
            "id": "f8b340d0-8c0c-41f8-acb5-662c676e2bbd",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_references": {
            "id": "8b2572ce-d118-41c4-b5d7-59f4ffe44431",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_community": {
            "id": "1b93fcd1-c6cd-432a-b831-a0fb680e327e",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_status": {
            "id": "036fa233-c42a-4fc6-861a-ff40450efc7d",
            "type": "category",
            "key": "tid",
        },
        "field_type": {
            "id": "7d69aeec-009d-4de2-8dd2-6b0aacb4578f",
            "type": "category",
            "key": "tid",
        },
        "field_proposal_focus": {
            "id": "328590d3-fefd-410d-b745-12f2efdd5437",
            "type": "category",
            "key": "tid",
        },
        "field_proposal_beneficiaries": {
            "id": "f18f0399-538b-4bf3-9cd5-4457138814a8",
            "type": "category",
            "key": "tid",
        },
        "field_proposal_theme": {
            "id": "a9b2b6de-fb7b-4709-aa59-f0ad987a677a",
            "type": "category",
            "key": "tid",
        },
        "field_technology_attribute": {
            "id": "251cf41a-0a49-4725-8d5a-5e496d018647",
            "type": "category",
            "key": "tid",
        },
        "field_term_region": {
            "id": "ed6244ae-6903-4412-8b7a-c219ed25dfbb",
            "type": "category",
            "key": "tid",
        },
        "field_term_country": {
            "id": "4b79c527-bf24-47f1-87a7-39945e70caeb",
            "type": "category",
            "key": "tid",
        },
        "field_proposal_upload": {
            "id": "6bec61a1-3527-4e21-aa65-f26d845bbb68",
            "type": "file",
            # TODO: finish mapping
        },
        "field_proposal_comments": {
            "id": "c0ff8444-8d43-46ef-8498-ed1a32c09c6a",
            "type": "value",
            "key": "safe_value",
        },
    }
