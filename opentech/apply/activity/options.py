from enum import Enum


class MESSAGES(Enum):
    UPDATE_LEAD = 'Update Lead'
    EDIT = 'Edit'
    APPLICANT_EDIT = "Applicant Edit"
    NEW_SUBMISSION = 'New Submission'
    SCREENING = 'Screening'
    TRANSITION = 'Transition'
    BATCH_TRANSITION = 'Batch Transition'
    DETERMINATION_OUTCOME = 'Determination Outcome'
    INVITED_TO_PROPOSAL = 'Invited To Proposal'
    REVIEWERS_UPDATED = 'Reviewers Updated'
    BATCH_REVIEWERS_UPDATED = 'Batch Reviewers Updated'
    READY_FOR_REVIEW = 'Ready For Review'
    NEW_REVIEW = 'New Review'
    COMMENT = 'Comment'
    PROPOSAL_SUBMITTED = 'Proposal Submitted'
    OPENED_SEALED = 'Opened Sealed Submission'

    @classmethod
    def choices(cls):
        return [
            (choice.name, choice.value)
            for choice in cls
        ]
