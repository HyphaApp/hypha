import { fetchSubmission, fetchSubmissionsByRound } from '@api/submissions';
import { createNoteForSubmission, fetchNotesForSubmission } from '@api/notes';

export default {
    fetchSubmissionsByRound,
    fetchSubmission,

    fetchNotesForSubmission,
    createNoteForSubmission,
};
