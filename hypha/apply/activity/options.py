from django.db.models import TextChoices
from django.utils.translation import gettext as _


class MESSAGES(TextChoices):
    # Format: {Python Value} = {DB Value} {Display Text or Verb}
    UPDATE_LEAD = "UPDATE_LEAD", _("updated lead")
    BATCH_UPDATE_LEAD = "BATCH_UPDATE_LEAD", _("batch updated lead")
    EDIT_SUBMISSION = "EDIT_SUBMISSION", _("edited submission")
    APPLICANT_EDIT = "APPLICANT_EDIT", _("edited applicant")
    NEW_SUBMISSION = "NEW_SUBMISSION", _("submitted new submission")
    DRAFT_SUBMISSION = "DRAFT_SUBMISSION", _("submitted new draft submission")
    SCREENING = "SCREENING", _("screened")
    TRANSITION = "TRANSITION", _("transitioned")
    BATCH_TRANSITION = "BATCH_TRANSITION", _("batch transitioned")
    DETERMINATION_OUTCOME = "DETERMINATION_OUTCOME", _("sent determination outcome")
    BATCH_DETERMINATION_OUTCOME = (
        "BATCH_DETERMINATION_OUTCOME",
        _("sent batch determination outcome"),
    )
    INVITED_TO_PROPOSAL = "INVITED_TO_PROPOSAL", _("invited to proposal")
    REVIEWERS_UPDATED = "REVIEWERS_UPDATED", _("updated reviewers")
    BATCH_REVIEWERS_UPDATED = "BATCH_REVIEWERS_UPDATED", _("batch updated reviewers")
    PARTNERS_UPDATED = "PARTNERS_UPDATED", _("updated partners")
    PARTNERS_UPDATED_PARTNER = "PARTNERS_UPDATED_PARTNER", _("partners updated partner")
    READY_FOR_REVIEW = "READY_FOR_REVIEW", _("marked ready for review")
    BATCH_READY_FOR_REVIEW = (
        "BATCH_READY_FOR_REVIEW",
        _("marked batch ready for review"),
    )
    NEW_REVIEW = "NEW_REVIEW", _("added new review")
    COMMENT = "COMMENT", _("added comment")
    PROPOSAL_SUBMITTED = "PROPOSAL_SUBMITTED", _("submitted proposal")
    OPENED_SEALED = "OPENED_SEALED", _("opened sealed submission")
    REVIEW_OPINION = "REVIEW_OPINION", _("reviewed opinion")
    DELETE_SUBMISSION = "DELETE_SUBMISSION", _("deleted submission")
    DELETE_REVIEW = "DELETE_REVIEW", _("deleted review")
    DELETE_REVIEW_OPINION = "DELETE_REVIEW_OPINION", _("deleted review opinion")
    CREATED_PROJECT = "CREATED_PROJECT", _("created project")
    UPDATED_VENDOR = "UPDATED_VENDOR", _("updated contracting information")
    UPDATE_PROJECT_LEAD = "UPDATE_PROJECT_LEAD", _("updated project lead")
    EDIT_REVIEW = "EDIT_REVIEW", _("edited review")
    SEND_FOR_APPROVAL = "SEND_FOR_APPROVAL", _("sent for approval")
    APPROVE_PROJECT = "APPROVE_PROJECT", _("approved project")
    ASSIGN_PAF_APPROVER = "ASSIGN_PAF_APPROVER", _("assign paf approver")
    APPROVE_PAF = "APPROVE_PAF", _("approved paf")
    PROJECT_TRANSITION = "PROJECT_TRANSITION", _("transitioned project")
    REQUEST_PROJECT_CHANGE = "REQUEST_PROJECT_CHANGE", _("requested project change")
    SUBMIT_CONTRACT_DOCUMENTS = (
        "SUBMIT_CONTRACT_DOCUMENTS",
        _("submitted contract documents"),
    )
    UPLOAD_DOCUMENT = "UPLOAD_DOCUMENT", _("uploaded document to project")
    REMOVE_DOCUMENT = "REMOVE_DOCUMENT", _("removed document from project")
    UPLOAD_CONTRACT = "UPLOAD_CONTRACT", _("uploaded contract to project")
    APPROVE_CONTRACT = "APPROVE_CONTRACT", _("approved contract")
    CREATE_INVOICE = "CREATE_INVOICE", _("created invoice for project")
    UPDATE_INVOICE_STATUS = "UPDATE_INVOICE_STATUS", _("updated invoice status")
    APPROVE_INVOICE = "APPROVE_INVOICE", _("approve invoice")
    DELETE_INVOICE = "DELETE_INVOICE", _("deleted invoice")
    SENT_TO_COMPLIANCE = "SENT_TO_COMPLIANCE", _("sent project to compliance")
    UPDATE_INVOICE = "UPDATE_INVOICE", _("updated invoice")
    SUBMIT_REPORT = "SUBMIT_REPORT", _("submitted report")
    SKIPPED_REPORT = "SKIPPED_REPORT", _("skipped report")
    REPORT_FREQUENCY_CHANGED = "REPORT_FREQUENCY_CHANGED", _("changed report frequency")
    DISABLED_REPORTING = "DISABLED_REPORTING", _("disabled reporting")
    REPORT_NOTIFY = "REPORT_NOTIFY", _("notified report")
    CREATE_REMINDER = "CREATE_REMINDER", _("created reminder")
    DELETE_REMINDER = "DELETE_REMINDER", _("deleted reminder")
    REVIEW_REMINDER = "REVIEW_REMINDER", _("reminder to review")
    BATCH_DELETE_SUBMISSION = "BATCH_DELETE_SUBMISSION", _("batch deleted submissions")
    BATCH_ARCHIVE_SUBMISSION = (
        "BATCH_ARCHIVE_SUBMISSION",
        _("batch archive submissions"),
    )
    BATCH_UPDATE_INVOICE_STATUS = (
        "BATCH_INVOICE_STATUS_UPDATE",
        _("batch update invoice status"),
    )
    STAFF_ACCOUNT_CREATED = "STAFF_ACCOUNT_CREATED", _("created new account")
    STAFF_ACCOUNT_EDITED = "STAFF_ACCOUNT_EDITED", _("edited account")
    ARCHIVE_SUBMISSION = "ARCHIVE_SUBMISSION", _("archived submission")
    UNARCHIVE_SUBMISSION = "UNARCHIVE_SUBMISSION", _("unarchived submission")
