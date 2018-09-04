from opentech.apply.review.management.commands.migration_review_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Fellowship (archive fund)"
    ROUND_NAME = "Fellowship (archive round)"
    APPLICATION_TYPE = "proposal"

    STREAMFIELD_MAP = {
        "field_fr_overall_no": {
            "id": "e68b6fe9-8b11-4cf0-8ae4-2ffed75e1e80",
            "type": "value",
            "key": "safe_value",
        },
        "field_fr_overall_yes": {
            "id": "a413f3a2-b486-4bf3-9e2d-c48d19626876",
            "type": "value",
            "key": "safe_value",
        },
        "field_fr_feedback": {
            "id": "comments",
            "type": "value",
            "key": "safe_value",
        },
        "field_fr_request_questions": {
            "id": "536c963a-f183-45bc-b83f-458b46dc5542",
            "type": "merge_value",
            "key": "safe_value",
        },
    }

    REQUEST_QUESTION_MAP = {
        "3618": {
            0: "Are the project objectives and timeline realistic?",
            1: "Should additional collaboration be included?",
            2: "Are the proposed outputs tailored to improve the likelihood of third party use such as utilizing more digestible and short form formats?",
            3: "Are there clear means of assessing the success of the project?",
            4: "General Comments",
        },
    }
