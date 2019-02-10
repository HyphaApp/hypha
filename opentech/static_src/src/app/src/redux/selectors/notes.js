import { createSelector } from 'reselect';

import { getSubmissionOfID } from '@selectors/submissions';

const getNotes = state => state.notes.byID;

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

const getNoteCreatingErrors = state => state.notes.createError;

export const getNoteCreatingErrorForSubmission = submissionID => createSelector(
    [getNoteCreatingErrors], errors => errors[submissionID]
);

const getNoteCreatingState = state => state.notes.isCreating;

export const getNoteCreatingStateForSubmission = submissionID => createSelector(
    [getNoteCreatingState], creatingStates => creatingStates.includes(submissionID)
);
