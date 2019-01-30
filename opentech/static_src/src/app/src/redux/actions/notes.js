import { CALL_API } from '@middleware/api'

import api from '@api';

export const FAIL_FETCHING_NOTES = 'FAIL_FETCHING_NOTES';
export const START_FETCHING_NOTES = 'START_FETCHING_NOTES';
export const UPDATE_NOTES = 'UPDATE_NOTES';
export const UPDATE_NOTE = 'UPDATE_NOTE';

export const START_CREATING_NOTE_FOR_SUBMISSION = 'START_CREATING_NOTE_FOR_SUBMISSION';
export const FAIL_CREATING_NOTE_FOR_SUBMISSION = 'FAIL_CREATING_NOTE_FOR_SUBMISSION';

export const fetchNotesForSubmission = submissionID => (dispatch, getState) => {
    return dispatch(fetchNotes(submissionID))
}

const fetchNotes = (submissionID) => ({
    [CALL_API]: {
        types: [ START_FETCHING_NOTES, UPDATE_NOTES, FAIL_FETCHING_NOTES],
        endpoint: api.fetchNotesForSubmission(submissionID),
    },
    submissionID,
})


export const createNoteForSubmission = (submissionID, note) => (dispatch, getState) => {
    return dispatch(createNote(submissionID, note))
}

const createNote = (submissionID, note) => ({
    [CALL_API]: {
        types: [ START_CREATING_NOTE_FOR_SUBMISSION, UPDATE_NOTE, FAIL_CREATING_NOTE_FOR_SUBMISSION],
        endpoint: api.createNoteForSubmission(submissionID, note),
    },
    submissionID,
})
