from opentech.apply.funds.management.commands.migration_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Fellowship archive fund"
    ROUND_NAME = "Fellowship archive round"
    APPLICATION_TYPE = "concept"

    STREAMFIELD_MAP = {
        "title": {
            "id": "title",
            "type": "direct",
        },
        "field_application_name": {
            "id": "full_name",
            "type": "value",
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
            "id": "duration",
            "type": "value",
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
            "type": "merge_value",
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

    REQUEST_QUESTION_MAP = {
        "3618": {
            0: "What will be the outcome(s) of your research?",
            1: "How will the results of your research be accessible to a non-technical audience?",
            2: "How will your work build on the existing research in your area of focus?",
            3: "Why is the organization chosen well suited to host your project?",
            4: "Please include a resume or CV (Feel free to attach a file at the bottom of the application)",
        },
        "3667": {
            0: "Does your fellowship project address an urgent and time-bound digital emergency? If so, how? ",
            1: "What steps will you take post-emergency to prevent a similar problem from occurring again in the future? ",
        },
        "3681": {
            0: "How does your fellowship project idea address the digital security threats the host organization(s) face?",
            1: "What are the anticipated results from your fellowship project?",
            2: "How will the results of your fellowship project be accessible to internet freedom technology developer community?",
            3: "Why is the organization(s) chosen well suited for your idea under the DIFP remit?",
            4: "Please include a resume or CV (Feel free to attach a file at the bottom of the application)",
        },
        "3861": {
            0: "Where are you located or would you like to be located during this fellowship?",
            1: "When would you ideally start and why?",
            2: "Please list any links to your portfolio or prior work",
        },
    }
