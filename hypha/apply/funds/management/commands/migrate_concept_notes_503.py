from opentech.apply.funds.management.commands.migration_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Core Infrastructure Fund"
    ROUND_NAME = "CIFund-2018-09"
    APPLICATION_TYPE = "concept"

    STREAMFIELD_MAP = {
        "title": {
            "id": "title",
            "type": "direct",
        },
        "field_concept_name": {
            "id": "full_name",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_mail": {
            "id": "email",
            "type": "value",
            "key": "email",
        },
        "field_concept_preapplied": {
            "id": "0305a465-8763-4c1f-9197-4ca4227d452a",
            "type": "map",
            "map": {
                "0": "No",
                "1": "Yes",
            },
        },
        "field_concept_preapplied_how": {
            "id": "c24691be-9861-4dbc-8be4-03b6e68c1973",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_description": {
            "id": "c21c58c3-cfbe-4409-b2f2-8f56398f1731",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_outcome": {
            "id": "27289c14-6926-4f61-bea2-8031a653f71c",
            "type": "value",
            "key": "safe_value",
        },
        "field_type": {
            "id": "404e2310-000b-4ccb-b772-3680946ff07d",
            "type": "category",
            "key": "tid",
        },
        "field_proposal_status": {
            "id": "145c364f-e0bb-4652-94e8-fe08c831da2b",
            "type": "category",
            "key": "tid",
        },
        "field_technology_attribute": {
            "id": "b4da2310-9654-4aa7-a04a-06335967ddc5",
            "type": "category",
            "key": "tid",
        },
        "field_concept_how": {
            "id": "418b8099-4525-437f-a55c-9b35745d0384",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_focus": {
            "id": "390702bd-e4e1-4dc2-8c43-d51bf018b427",
            "type": "category",
            "key": "tid",
        },
        "field_concept_time": {
            "id": "duration",
            "type": "value",
        },
        "field_concept_amount": {
            "id": "value",
            "type": "value",
        },
        "field_concept_how_long": {
            "id": "dfb9c307-9328-4a99-9efc-321d474b2ba7",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_who": {
            "id": "11f94a22-0571-4491-a93e-87c050e02a4a",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_community": {
            "id": "c272969b-d89f-4b6e-859f-4606a15b3f28",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_beneficiaries": {
            "id": "72002c3e-aaee-47da-9377-8bb493f14c21",
            "type": "category",
            "key": "tid",
        },
        "field_term_region": {
            "id": "369b248e-f669-4aeb-b771-7cba0eadb921",
            "type": "category",
            "key": "tid",
        },
        "field_term_country": {
            "id": "57bceb33-ebda-4708-9080-fd1a5923e008",
            "type": "category",
            "key": "tid",
        },
        "field_concept_why": {
            "id": "c14ee077-c0eb-48b1-9825-fbba9b91ede5",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_theme": {
            "id": "a83a1884-f711-4196-8d15-ae2110466acb",
            "type": "category",
            "key": "tid",
        },
        "field_proposal_similar_efforts": {
            "id": "9ca35708-d611-4cd0-8d4a-3cc08349f45b",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_contact": {
            "id": "db7b1642-c03d-4af4-82c9-db67bf9713b0",
            "type": "value",
            "key": "safe_value",
        },
        "field_concept_upload": {
            "id": "8a91231c-5c3d-46fe-9de6-8d5c86817626",
            "type": "file",
            # TODO: finish mapping
        },
        "field_application_otf_mission": {
            "id": "4c661a64-2614-4169-b4d2-1fd39e2e831b",
            "type": "boolean",
        },
        "field_application_otf_tos": {
            "id": "1bc4e113-1414-46ff-bba7-2dc02b2126df",
            "type": "boolean",
        },
        "field_application_otf_represent": {
            "id": "42dd68a1-b699-4678-bea6-13e0f842e821",
            "type": "boolean",
        },
        "field_application_otf_license": {
            "id": "72916731-ec97-4688-95f1-d3bf140b03c2",
            "type": "boolean",
        },
        "field_application_otf_complete": {
            "id": "6856d26d-b169-4fdf-b598-63c3dd9278a2",
            "type": "boolean",
        },
        "field_application_otf_deadline": {
            "id": "33838399-f292-4b63-83f0-e02d344f99d4",
            "type": "boolean",
        },
        "field_application_otf_list": {
            "id": "fc571e12-d4a2-4d53-ab34-2c57321dc6ac",
            "type": "boolean",
        },
        "field_application_otf_newsletter": {
            "id": "cd0d8a4b-e71a-4dff-964a-f547bd655e7d",
            "type": "boolean",
        },
    }
