import { fetchSubmission, fetchSubmissionsByRound } from '@api/submissions';
import { fetchRound } from '@api/rounds';
import { createNoteForSubmission, fetchNotesForSubmission } from '@api/notes';

export default {
    fetchSubmissionsByRound,
    fetchSubmission,

    fetchRound,

    fetchNotesForSubmission,
    createNoteForSubmission,
};
