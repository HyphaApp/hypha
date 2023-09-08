from hypha.apply.funds.management.commands.migration_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Fellowship (archive fund)"
    ROUND_NAME = "Fellowship (archive round)"
    APPLICATION_TYPE = "proposal"

    STREAMFIELD_MAP = {
        "title": {
            "id": "title",
            "type": "direct",
        },
        "field_proposal_common_name": {
            "id": "full_name",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_host_text": {
            "id": "bc03235e-3c78-4770-9fc2-97feb93c2c8c",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_start_date": {
            "id": "672cb6f1-335c-4005-a0f1-46c414feda06",
            "type": "value",
            "key": "value",
        },
        "field_proposal_completion_date": {
            "id": "8262f209-f084-4a79-9dfa-2d18137119bb",
            "type": "value",
            "key": "value",
        },
        "field_proposal_objectives": {
            "id": "af2c5f38-7257-4295-87fa-787060e845ef",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_activities": {
            "id": "3c521847-7642-4cae-aca9-d5336ad8962d",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_sustainability": {
            "id": "fd0eb7ea-e054-4bcf-9580-eb672d44745c",
            "type": "value",
            "key": "safe_value",
        },
        "field_proposal_request_questions": {
            "id": "b6d71932-98c2-4ce8-a5e6-454a1f800d21",
            "type": "merge_value",
            "key": "safe_value",
        },
        "field_proposal_upload": {
            "id": "30dfa46e-f656-46c9-9efc-bab9029f2008",
            "type": "file",
            # TODO: finish mapping
        },
    }

    REQUEST_QUESTION_MAP = {
        "3618": {
            0: "How will this project leverage the resources made available by the host organization?",
            1: "Please detail the specific steps the applicant will take to ensure the project outcomes reach non-technical audiences",
            2: "In what ways will this effort advance understanding in the relevant field?",
            3: "What risks or variables could jeopardize either the outcomes of the project or the safety of the applicant?",
            4: "How is the applicant well equipped to carry out the technical work proposed? (if applicable)",
        },
        "3681": {
            0: "Please detail the specific steps the applicant will take to ensure the project outcomes reach the internet freedom technology community.",
            1: "What risks could jeopardize the fellowship project?",
            2: "How would those risks be mitigated or addressed?",
            3: "How will your work be sustained following the completion of your fellowship?",
            4: "If your project includes public gatherings, do you have a code of conduct? If yes, please list below or provide links to where it can be publicly accessed.",
            5: "Please include letters of support for the organization or organizations you would be working with (Please attach a file at the bottom of the application)",
        },
    }
