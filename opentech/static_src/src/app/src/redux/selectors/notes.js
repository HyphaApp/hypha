import { createSelector } from 'reselect';

import { getSubmissionOfID } from '@selectors/submissions';

const getNotes = state => state.notes.byID;

export const getNoteOfID = (noteID) => createSelector(
    [getNotes], notes => notes[noteID]
);

export const getNotesFetchState = state => state.notes.isFetching === true;

export const getNotesErrorState = state => state.notes.isErrored === true;

export const getNoteIDsForSubmissionOfID = submissionID => createSelector(
    [getSubmissionOfID(submissionID)],
    submission => (submission || {}).comments || []
);

const getNoteCreatingErrors = state => state.notes.createError;

export const getNoteCreatingErrorForSubmission = submissionID => createSelector(
    [getNoteCreatingErrors], errors => errors[submissionID]
);

const getNoteCreatingState = state => state.notes.isCreating;

export const getNoteCreatingStateForSubmission = submissionID => createSelector(
    [getNoteCreatingState], creatingStates => creatingStates.includes(submissionID)
);
