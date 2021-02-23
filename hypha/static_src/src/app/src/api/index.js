import {
    executeSubmissionAction,
    updateSummaryEditor,
    fetchSubmission,
    fetchSubmissionsByRound,
    fetchSubmissionsByStatuses,
    fetchReviewDraft,
    fetchDeterminationDraft,
} from '@api/submissions';
import { fetchRound, fetchRounds } from '@api/rounds';
import { createNoteForSubmission, fetchNotesForSubmission, fetchNewNotesForSubmission, editNoteForSubmission } from '@api/notes';

export default {
    executeSubmissionAction,
    updateSummaryEditor,
    fetchSubmissionsByRound,
    fetchSubmissionsByStatuses,
    fetchSubmission,
    fetchReviewDraft,
    fetchDeterminationDraft,

    fetchRound,
    fetchRounds,

    fetchNotesForSubmission,
    fetchNewNotesForSubmission,
    createNoteForSubmission,
    editNoteForSubmission,
};
