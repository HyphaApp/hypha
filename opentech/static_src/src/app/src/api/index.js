import { fetchSubmission, fetchSubmissionsByRound, fetchSubmissionsByStatuses } from '@api/submissions';
import { fetchRound, fetchRounds } from '@api/rounds';
import { createNoteForSubmission, fetchNotesForSubmission } from '@api/notes';

export default {
    fetchSubmissionsByRound,
    fetchSubmissionsByStatuses,
    fetchSubmission,

    fetchRound,
    fetchRounds,

    fetchNotesForSubmission,
    createNoteForSubmission,
};
