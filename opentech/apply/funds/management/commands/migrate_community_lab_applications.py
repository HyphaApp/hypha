from opentech.apply.funds.management.commands.migration_base import MigrateCommand


class Command(MigrateCommand):
    LAB_NAME = "Community lab"
    APPLICATION_TYPE = "request"
    CONTENT_TYPE = "lab"

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
            "id": "d3364b5b-976b-4cd6-85d5-4ccc0bb9b560",
            "type": "value",
            "key": "value",
        },
        "field_application_amount": {
            "id": "value",
            "type": "value",
        },
        "field_application_amount_text": {
            "id": "value",
            "type": "value",
        },
        "field_application_describe": {
            "id": "aeea7bd9-01b5-406e-bb30-1303ba0f550a",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_who": {
            "id": "a5117396-0286-4937-91a3-be33a5944ac6",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_objective_text": {
            "id": "d90d2cd4-831e-46f5-8f2e-82ac94913784",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_strategy": {
            "id": "fc5ddac7-c7b5-4d07-9bc3-16902e9a7afb",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_how": {
            "id": "ea6ceb76-882e-4739-94da-7b055a112d1c",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_collaboration": {
            "id": "afa7e16b-d31c-4016-af88-7939acc7b6e1",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_diverse": {
            "id": "55e23c45-72a7-4ab9-9940-764d00724de8",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_outreach": {
            "id": "737bd894-78b1-41ef-969c-2a57c843cd5b",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_needs": {
            "id": "56c84f40-f59e-4e82-80a1-2cd971717e9c",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_budget": {
            "id": "6ca29ae0-780a-467a-a3e9-34195bcb0d79",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_cod": {
            "id": "9db8b2ca-62b6-44c4-9d3d-70cb4a28e65f",
            "type": "boolean",
        },
        "field_concept_upload": {
            "id": "b3af7aac-3439-45fa-9573-518f82f5cd6c",
            "type": "file",
            # TODO: finish mapping
        },
        "field_application_otf_mission": {
            "id": "1248f597-2f18-4b16-8f96-63912e5197c5",
            "type": "boolean",
        },
        "field_application_otf_tos": {
            "id": "5a676552-e189-417e-9901-05bfc973cfb5",
            "type": "boolean",
        },
        "field_application_otf_represent": {
            "id": "c4f54c3d-6b2a-4b32-b651-9121430aa06f",
            "type": "boolean",
        },
        "field_application_otf_license": {
            "id": "beb4d454-466d-43d5-823e-80dbccacbbb3",
            "type": "boolean",
        },
        "field_application_otf_complete": {
            "id": "fd6b034d-7cec-49fe-b4da-991c382283ef",
            "type": "boolean",
        },
        "field_application_otf_deadline": {
            "id": "d930a864-263d-4d0d-8ff1-553b13efda41",
            "type": "boolean",
        },
        "field_application_otf_list": {
            "id": "f75fd335-be7d-460d-b96a-53d7aa9a826f",
            "type": "boolean",
        },
        "field_application_otf_newsletter": {
            "id": "a1f03bca-9267-49cf-9880-444d6806065c",
            "type": "boolean",
        },

    }
