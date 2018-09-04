from opentech.apply.review.management.commands.migration_review_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Internet Freedom Fund (archive fund)"
    ROUND_NAME = "Internet Freedom Fund (archive round)"
    APPLICATION_TYPE = "proposal"

    STREAMFIELD_MAP = {
        "field_pr_confidentiality": {
            "id": "65fb2c22-a0c5-4cde-94a7-feb27072bc3d",
            "type": "boolean",
        },
        "field_pr_conflicts": {
            "id": "dd75ce49-e3c4-43da-b724-4cb8bb88dcf8",
            "type": "map",
            "map": {
                "0": "No",
                "1": "Yes",
            },
        },
        "field_pr_disclosure": {
            "id": "9f7fe70b-97b5-4263-98ac-a45bf97b59d0",
            "type": "value",
            "key": "safe_value",
        },
        "field_pr_liked": {
            "id": "e91ed603-61ad-483e-be7b-21716d05a3bd",
            "type": "value",
            "key": "safe_value",
        },
        "field_pr_concern": {
            "id": "821fb071-7db7-4cc1-ac3a-34b9eee40c94",
            "type": "value",
            "key": "safe_value",
        },
        "field_pr_red_flags": {
            "id": "021624ac-6628-430d-ba86-e68fd518c87e",
            "type": "value",
            "key": "safe_value",
        },
        "field_pr_overview_rate": {
            "id": "9c5603d5-f897-42fa-8739-5935769c94bd",
            "type": "score",
        },
        "field_pr_objectives_rate": {
            "id": "6b748400-fad9-4b31-bb85-e3a53c99f4df",
            "type": "score",
        },
        "field_pr_strategy_rate": {
            "id": "a806a944-1d8a-4904-ace0-acfce5634a50",
            "type": "score",
        },
        "field_pr_technical_rate": {
            "id": "512a86a5-ec5b-4d36-9630-90648b5b43e4",
            "type": "score",
        },
        "field_pr_alternative_rate": {
            "id": "d9695d1d-3373-4acf-ada5-3b2593b3a634",
            "type": "score",
        },
        "field_pr_usability_rate": {
            "id": "e43dd4dc-d2fa-493c-9f55-5a126d0e0579",
            "type": "score",
        },
        "field_pr_sustainability_rate": {
            "id": "ee7009b8-ad18-46b5-a981-ccc52972c0a5",
            "type": "score",
        },
        "field_pr_collaboration_rate": {
            "id": "dc5dc5e0-e4d6-462f-8296-a0e58933e701",
            "type": "score",
        },
        "field_pr_realism_rate": {
            "id": "31e9b202-24b1-4993-80b7-9851624e2162",
            "type": "score",
        },
        "field_pr_qualifications_rate": {
            "id": "d3f5479c-68da-41d9-a266-130d383bab6b",
            "type": "score",
        },
        "field_pr_evaluation_rate": {
            "id": "2a61c71a-74f6-4963-8850-9289e852f604",
            "type": "score",
        },
        "field_pr_rationale_rate": {
            "id": "0d1bf533-968c-44b9-bb30-d437ae039474",
            "type": "score",
        },
        "field_pr_overview": {
            "id": "9c5603d5-f897-42fa-8739-5935769c94bd",
            "type": "placeholder",
        },
        "field_pr_objectives": {
            "id": "6b748400-fad9-4b31-bb85-e3a53c99f4df",
            "type": "placeholder",
        },
        "field_pr_strategy": {
            "id": "a806a944-1d8a-4904-ace0-acfce5634a50",
            "type": "placeholder",
        },
        "field_pr_technical": {
            "id": "512a86a5-ec5b-4d36-9630-90648b5b43e4",
            "type": "placeholder",
        },
        "field_pr_alternative": {
            "id": "d9695d1d-3373-4acf-ada5-3b2593b3a634",
            "type": "placeholder",
        },
        "field_pr_usability": {
            "id": "e43dd4dc-d2fa-493c-9f55-5a126d0e0579",
            "type": "placeholder",
        },
        "field_pr_sustainability": {
            "id": "ee7009b8-ad18-46b5-a981-ccc52972c0a5",
            "type": "placeholder",
        },
        "field_pr_collaboration": {
            "id": "dc5dc5e0-e4d6-462f-8296-a0e58933e701",
            "type": "placeholder",
        },
        "field_pr_realism": {
            "id": "31e9b202-24b1-4993-80b7-9851624e2162",
            "type": "placeholder",
        },
        "field_pr_qualifications": {
            "id": "d3f5479c-68da-41d9-a266-130d383bab6b",
            "type": "placeholder",
        },
        "field_pr_evaluation": {
            "id": "2a61c71a-74f6-4963-8850-9289e852f604",
            "type": "placeholder",
        },
        "field_pr_rationale": {
            "id": "0d1bf533-968c-44b9-bb30-d437ae039474",
            "type": "placeholder",
        },
        "field_pr_recommendation_comments": {
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
