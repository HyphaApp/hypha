from enum import Enum


class MESSAGES(Enum):
    UPDATE_LEAD = 'Update Lead'
    BATCH_UPDATE_LEAD = 'Batch Update Lead'
    EDIT = 'Edit'
    APPLICANT_EDIT = "Applicant Edit"
    NEW_SUBMISSION = 'New Submission'
    SCREENING = 'Screening'
    TRANSITION = 'Transition'
    BATCH_TRANSITION = 'Batch Transition'
    DETERMINATION_OUTCOME = 'Determination Outcome'
    BATCH_DETERMINATION_OUTCOME = 'Batch Determination Outcome'
    INVITED_TO_PROPOSAL = 'Invited To Proposal'
    REVIEWERS_UPDATED = 'Reviewers Updated'
    BATCH_REVIEWERS_UPDATED = 'Batch Reviewers Updated'
    PARTNERS_UPDATED = 'Partners Updated'
    PARTNERS_UPDATED_PARTNER = 'Partners Updated Partner'
    READY_FOR_REVIEW = 'Ready For Review'
    BATCH_READY_FOR_REVIEW = 'Batch Ready For Review'
    NEW_REVIEW = 'New Review'
    COMMENT = 'Comment'
    PROPOSAL_SUBMITTED = 'Proposal Submitted'
    OPENED_SEALED = 'Opened Sealed Submission'
    REVIEW_OPINION = 'Review Opinion'
    DELETE_SUBMISSION = 'Delete Submission'
    DELETE_REVIEW = 'Delete Review'
    CREATED_PROJECT = 'Created Project'
    UPDATE_PROJECT_LEAD = 'Update Project Lead'
    EDIT_REVIEW = 'Edit Review'
    SEND_FOR_APPROVAL = 'Send for Approval'
    APPROVE_PROJECT = 'Project was Approved'
    REQUEST_PROJECT_CHANGE = 'Project change requested'
    UPLOAD_DOCUMENT = 'Document was Uploaded to Project'
    REMOVE_DOCUMENT = 'Document was Removed from Project'

    @classmethod
    def choices(cls):
        return [
            (choice.name, choice.value)
            for choice in cls
        ]
