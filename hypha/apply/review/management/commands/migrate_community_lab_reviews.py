from opentech.apply.review.management.commands.migration_review_base import MigrateCommand


class Command(MigrateCommand):
    LAB_NAME = "Community lab (archive fund)"
    APPLICATION_TYPE = "request"
    CONTENT_TYPE = "lab"

    STREAMFIELD_MAP = {
        "field_pr_confidentiality": {
            "id": "c1c6cedc-a084-4c55-87d5-7f6baf48441e",
            "type": "boolean",
        },
        "field_pr_conflicts": {
            "id": "c29a7f43-009c-4341-bbe8-9582ba089d52",
            "type": "map",
            "map": {
                "0": "No",
                "1": "Yes",
            },
        },
        "field_pr_disclosure": {
            "id": "3aab69b1-6b60-4850-8f9f-7bc1b5871dcf",
            "type": "value",
            "key": "safe_value",
        },
        "field_clr_remit_rate": {
            "id": "732fc004-3086-44e1-8508-e0f17c3732a8",
            "type": "score",
        },
        "field_clr_like": {
            "id": "f3c42cf1-e5ef-4674-bf6c-8e4640ee0d58",
            "type": "value",
            "key": "safe_value",
        },
        "field_clr_not_like": {
            "id": "e1e69628-c663-4cd2-a0ea-507ad01149de",
            "type": "value",
            "key": "safe_value",
        },
        "field_clr_information": {
            "id": "3033f228-58af-4944-b884-736fe6258bd6",
            "type": "value",
            "key": "safe_value",
        },
        "field_clr_voices": {
            "id": "20ec1ed7-4e3e-433c-944a-7c20cd6245c8",
            "type": "value",
            "key": "safe_value",
        },
        "field_clr_reach_out": {
            "id": "fd361c53-a263-4572-8403-74f6736d38fc",
            "type": "value",
            "key": "safe_value",
        },
    }
