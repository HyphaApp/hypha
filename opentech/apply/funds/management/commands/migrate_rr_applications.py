from opentech.apply.funds.management.commands.migration_base import MigrateCommand


class Command(MigrateCommand):
    CONTENT_TYPE = "fund"
    FUND_NAME = "Rapid Response (archive fund)"
    ROUND_NAME = "Rapid Response (archive round)"
    APPLICATION_TYPE = "request"

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
        "field_application_preapplied": {
            "id": "49a0f5f4-e8e9-4dfc-8575-205ee9675032",
            "type": "map",
            "map": {
                "0": "No",
                "1": "Yes",
            },
        },
        "field_application_apply_for": {
            "id": "c1277029-1718-40e3-8bf5-d80ece7fd343",
            "type": "map",
            "map": {
                "direct": "Direct funding",
                "receive": "Requesting to receive services",
                "provide": "Requesting to provide services",
            },
        },
        "field_application_amount": {
            "id": "value",
            "type": "value",
        },
        "field_application_amount_text": {
            "id": "value",
            "type": "value",
        },
        "field_application_service": {
            "id": "ebdf9a22-58c7-4bd6-a58d-e71363357470",
            "type": "map",
            "map": {
                "audit": "Audit of presumably compromised websites",
                "ddos": "DDoS response and mitigation",
                "hosting": "Secure web hosting",
                "hostingevents": "Secure hosting for monitoring and resiliency of websites during special events (elections, campaigns etc.)",
                "vpn": "VPN connections",
                "isp": "Safe internet connections",
                "analysis": "Forensic analysis of digital attacks",
                "recovery": "Recovery of compromised websites",
                "malware": "Malware analysis",
                "equipment": "Equipment replacements (unavailable)",
                "legalhelp": "Finding legal representation (unavailable)",
                "legalfees": "Payment of legal fees (unavailable)",
            },
        },
        "field_application_service_other": {
            "id": "c8c329c7-78e4-4cbf-a3b1-77a1324e92ff",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_duration3": {
            "id": "duration",
            "type": "value",
        },
        "field_application_who": {
            "id": "1ec16cdc-7a68-40be-b17b-9a218def4260",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_how": {
            "id": "4fa2ac11-d1cd-4d23-8082-93a14c8f99c8",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_sustainability": {
            "id": "3cde39ae-b687-4c4f-b58b-849396c2fdb8",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_dates": {
            "id": "0b2a4653-b390-44a6-b92e-fae4647e7ec4",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_why": {
            "id": "6d75e412-cf53-4833-9f1d-3e0126512fb9",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_why_rapiid": {
            "id": "1b181d1e-ef91-41af-b9c1-d096a991314b",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_focus": {
            "id": "efd91eaf-378f-4aab-96cb-c5601155cbee",
            "type": "category",
            "key": "tid",
        },
        "field_application_objectives": {
            "id": "4be0c7bd-231d-4d9f-bd47-8589fc005f54",
            "type": "category",
            "key": "tid",
        },
        "field_application_beneficiaries": {
            "id": "6e0293ee-218e-4c3b-b82d-5bf91fdb21c9",
            "type": "category",
            "key": "tid",
        },
        "field_term_region": {
            "id": "6ff029c6-c6d1-4c37-a49a-46181b1cd33d",
            "type": "category",
            "key": "tid",
        },
        "field_application_problems": {
            "id": "7fb1001e-d458-414f-a5bb-006db6f89baf",
            "type": "category",
            "key": "tid",
        },
        "field_application_budget": {
            "id": "45d7d38a-9c9d-4c43-98df-bb95d4a1dd77",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_legal_name": {
            "id": "632065c5-860f-4751-9b31-52914d7c6448",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_contact": {
            "id": "13bb0d64-65f3-4340-8e7e-e5da80d706d5",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_phone": {
            "id": "2cb9fe4b-df45-4181-80e5-14382f853081",
            "type": "value",
            "key": "safe_value",
        },
        "field_application_address": {
            "id": "bd29eb88-9754-4305-9b2d-406a875ec56a",
            "type": "address",
            "map": {
                "administrative_area": "administrativearea",
                "country": "country",
                "locality": "localityname",
                "postal_code": "postalcode",
                "thoroughfare": "thoroughfare",
                "premise": "premise",
            }
        },
        "field_application_questions": {
            "id": "1889de86-0a0d-4abf-9916-4db87a499d35",
            "type": "merge_value",
            "key": "safe_value",
        },
        "field_application_otf_mission": {
            "id": "e695f0d7-4c74-4cc6-853f-bd62ecd19d3d",
            "type": "boolean",
        },
        "field_application_otf_tos": {
            "id": "f40d1acc-d802-4cc6-b0e9-fff78dc54223",
            "type": "boolean",
        },
        "field_application_otf_represent": {
            "id": "0b3c0827-38e2-439b-bca5-735835af1019",
            "type": "boolean",
        },
        "field_application_otf_license": {
            "id": "bc9c960e-a6f4-4bc2-b626-efb5bc5552c6",
            "type": "boolean",
        },
        "field_application_otf_complete": {
            "id": "5812b66d-630e-4ca2-8bea-819084278f55",
            "type": "boolean",
        },
        "field_application_otf_deadline": {
            "id": "97d3746c-cf0f-449a-b3a3-7a9cdd45cc6d",
            "type": "boolean",
        },
        "field_application_otf_list": {
            "id": "fc3d2a87-1151-418b-b1cd-9289f00bde35",
            "type": "boolean",
        },
        "field_application_otf_newsletter": {
            "id": "83ecc69a-f47c-495e-bc8f-326e55aed67a",
            "type": "boolean",
        },
        "field_concept_upload": {
            "id": "607daeba-1f33-4ad0-b135-eda743ba8e3a",
            "type": "file",
            # TODO: finish mapping
        },
    }

    REQUEST_QUESTION_MAP = {
        "3618": {
            "0": "What will be the outcome(s) of your research?",
            "1": "How will the results of your research be accessible to a non-technical audience?",
            "2": "How will your work build on the existing research in your area of focus?",
            "3": "Why is the organization chosen well suited to host your project?",
            "4": "Please include a resume or CV (Feel free to attach a file at the bottom of the application)",
        },
        "3667": {
            "0": "Does your fellowship project address an urgent and time-bound digital emergency? If so, how? ",
            "1": "What steps will you take post-emergency to prevent a similar problem from occurring again in the future? ",
        },
        "3681": {
            "0": "How does your fellowship project idea address the digital security threats the host organization(s) face?",
            "1": "What are the anticipated results from your fellowship project?",
            "2": "How will the results of your fellowship project be accessible to internet freedom technology developer community?",
            "3": "Why is the organization(s) chosen well suited for your idea under the DIFP remit?",
            "4": "Please include a resume or CV (Feel free to attach a file at the bottom of the application)",
        },
        "3861": {
            "0": "Where are you located or would you like to be located during this fellowship?",
            "1": "When would you ideally start and why?",
            "2": "Please list any links to your portfolio or prior work",
        },
    }
