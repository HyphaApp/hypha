import {
    executeSubmissionAction,
    fetchSubmission,
    fetchSubmissionsByRound,
    fetchSubmissionsByStatuses,
    fetchReviewDraft
} from '@api/submissions';
import { fetchRound, fetchRounds } from '@api/rounds';
import { createNoteForSubmission, fetchNotesForSubmission, fetchNewNotesForSubmission, editNoteForSubmission } from '@api/notes';

export default {
    executeSubmissionAction,

    fetchSubmissionsByRound,
    fetchSubmissionsByStatuses,
    fetchSubmission,
    fetchReviewDraft,

    fetchRound,
    fetchRounds,

    fetchNotesForSubmission,
    fetchNewNotesForSubmission,
    createNoteForSubmission,
    editNoteForSubmission,
};
