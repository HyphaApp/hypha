from opentech.apply.review.management.commands.migration_review_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Fellowship (archive fund)"
    ROUND_NAME = "Fellowship (archive round)"
    APPLICATION_TYPE = "concept"

    STREAMFIELD_MAP = {
        "field_fr_overall_no": {
            "id": "f0533950-57f5-4bb7-81ec-2d3813490c88",
            "type": "value",
            "key": "safe_value",
        },
        "field_far_request_questions": {
            "id": "ba789376-e3f9-434e-8da5-330811723b30",
            "type": "merge_value",
            "key": "safe_value",
        },
    }

    REQUEST_QUESTION_MAP = {
        "3618": {
            0: "Do the Goals and principles of the application align with the program?",
            1: "Does the application propose a unique contribution to the relevant field?",
            2: "Do you consider the application reasonable and realistic?",
            3: "General Comments",
        },
        "3681": {
            0: "What are the positive aspects of this application?",
            1: "What are the negative aspects of this application?",
            2: "What items must the applicant address, if any?",
        },
    }
