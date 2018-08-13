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
            "id": "8c74af9c-6cc7-4558-9d72-0f2c9a87f22b",
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
