from opentech.apply.review.management.commands.migration_review_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Internet Freedom Fund (archive fund)"
    ROUND_NAME = "Internet Freedom Fund (archive round)"
    APPLICATION_TYPE = "concept"

    STREAMFIELD_MAP = {
        "field_pr_recommendation_comments": {
            "id": "f16be0b3-ef02-4876-b056-8a84238b1a52",
            "type": "value",
            "key": "safe_value",
        },
        "field_cnr_principles_rate": {
            "id": "6dd8d5d2-09a5-4681-aebc-eb9ccd00395a",
            "type": "score",
        },
        "field_cnr_technical_rate": {
            "id": "52b1f53c-9656-4b0c-8b8b-a9c57869356d",
            "type": "score",
        },
        "field_field_cnr_sustainable_rate": {
            "id": "aedb27e7-6044-4e04-b2c7-358065c8fe5c",
            "type": "score",
        },
        "field_cnr_principles": {
            "id": "6dd8d5d2-09a5-4681-aebc-eb9ccd00395a",
            "type": "placeholder",
        },
        "field_cnr_technical": {
            "id": "52b1f53c-9656-4b0c-8b8b-a9c57869356d",
            "type": "placeholder",
        },
        "field_cnr_sustainable": {
            "id": "aedb27e7-6044-4e04-b2c7-358065c8fe5c",
            "type": "placeholder",
        },
        "field_cnr_request_questions": {
            "id": "84405ba2-f94e-4d4d-92e1-190bd802f858",
            "type": "merge_value",
            "key": "safe_value",
        },
        "field_cnr_comments": {
            "id": "comments",
            "type": "value",
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
