import { CALL_API } from '@middleware/api'
import { getLatestNoteForSubmissionOfID } from '@selectors/notes'

import api from '@api';

export const FAIL_FETCHING_NOTES = 'FAIL_FETCHING_NOTES';
export const START_FETCHING_NOTES = 'START_FETCHING_NOTES';
export const UPDATE_NOTES = 'UPDATE_NOTES';
export const CREATE_NOTE = 'CREATE_NOTE';
export const UPDATE_NOTE = 'UPDATE_NOTE';
export const STORE_NOTE = 'UPDATE_STORE_NOTE';

export const START_CREATING_NOTE_FOR_SUBMISSION = 'START_CREATING_NOTE_FOR_SUBMISSION';
export const FAIL_CREATING_NOTE_FOR_SUBMISSION = 'FAIL_CREATING_NOTE_FOR_SUBMISSION';

export const START_EDITING_NOTE_FOR_SUBMISSION = 'START_EDITING_NOTE_FOR_SUBMISSION';
export const FAIL_EDITING_NOTE_FOR_SUBMISSION = 'FAIL_EDITING_NOTE_FOR_SUBMISSION';
export const REMOVE_NOTE = 'REMOVE_NOTE';

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
        types: [ START_CREATING_NOTE_FOR_SUBMISSION, CREATE_NOTE, FAIL_CREATING_NOTE_FOR_SUBMISSION],
        endpoint: api.createNoteForSubmission(submissionID, note),
    },
    submissionID,
})


export const fetchNewNotesForSubmission = (submissionID) => (dispatch, getState) => {
    const latestNoteID = getLatestNoteForSubmissionOfID(submissionID)(getState());
    if ( latestNoteID ) {
        return dispatch(fetchNewerNotes(submissionID, latestNoteID))
    } else {
        return dispatch(fetchNotes(submissionID))
    }
}


const fetchNewerNotes = (submissionID, latestID) => ({
    [CALL_API]: {
        types: [ START_FETCHING_NOTES, UPDATE_NOTES, FAIL_FETCHING_NOTES],
        endpoint: api.fetchNewNotesForSubmission(submissionID, latestID),
    },
    submissionID,
})


export const editingNote = (messageID, message, submissionID) => ({
    type: STORE_NOTE,
    messageID,
    submissionID,
    message
})


export const writingNote = (submissionID, message) => ({
    type: STORE_NOTE,
    submissionID,
    message

})


export const editNoteForSubmission = (note, submissionID) => (dispatch) => dispatch(editNote(note, submissionID))

const editNote = (note, submissionID) => ({
    [CALL_API]: {
        types: [ START_EDITING_NOTE_FOR_SUBMISSION, UPDATE_NOTE, FAIL_EDITING_NOTE_FOR_SUBMISSION ],
        endpoint: api.editNoteForSubmission(note),
    },
    note,
    submissionID,
})


export const removedStoredNote = (submissionID) => ({
    type: REMOVE_NOTE,
    submissionID,
})
