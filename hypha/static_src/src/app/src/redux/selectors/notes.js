import { createSelector } from 'reselect';

import { getSubmissionOfID } from '@selectors/submissions';

export const getNotes = state => state.notes.byID;

export const getNoteOfID = (noteID) => createSelector(
    [getNotes], notes => notes[noteID]
);

export const getNotesFetchState = state => state.notes.isFetching === true;

export const getNotesErrorState = state => state.notes.error.errored === true;

export const getNotesErrorMessage = state => state.notes.error.message;

export const getNoteIDsForSubmissionOfID = submissionID => createSelector(
    [getSubmissionOfID(submissionID)],
    submission => (submission || {}).comments || []
);

export const getLatestNoteForSubmissionOfID = submissionID => createSelector(
    [getNoteIDsForSubmissionOfID(submissionID)],
    notes => notes[0] || null
);

export const getNotesForSubmission = submissionID => createSelector(
    [getNoteIDsForSubmissionOfID(submissionID), getNotes],
    (noteIDs, notes) => noteIDs.map(noteID => notes[noteID])
);

export const getNoteCreatingErrors = state => state.notes.createError;

export const getNoteCreatingErrorForSubmission = submissionID => createSelector(
    [getNoteCreatingErrors], errors => errors[submissionID]
);

export const getNoteCreatingState = state => state.notes.isCreating;

export const getNoteCreatingStateForSubmission = submissionID => createSelector(
    [getNoteCreatingState], creatingStates => creatingStates.includes(submissionID)
);

export const getNoteEditingState = state => state.notes.editing;

export const getDraftNoteForSubmission = submissionID => createSelector(
    [getNoteEditingState], editing => editing[submissionID]
);
