import { updateSubmission, appendNoteIDForSubmission } from '@actions/submissions';
import api from '@api';

export const FAIL_FETCHING_NOTES = 'FAIL_FETCHING_NOTES';
export const START_FETCHING_NOTES = 'START_FETCHING_NOTES';
export const UPDATE_NOTES = 'UPDATE_NOTES';
export const UPDATE_NOTE = 'UPDATE_NOTE';

export const START_CREATING_NOTE_FOR_SUBMISSION = 'START_CREATING_NOTE_FOR_SUBMISSION';
export const FAIL_CREATING_NOTE_FOR_SUBMISSION = 'FAIL_CREATING_NOTE_FOR_SUBMISSION';

const startFetchingNotes = () => ({
    type: START_FETCHING_NOTES,
});

const failFetchingNotes = message => ({
    type: FAIL_FETCHING_NOTES,
    message,
});

export const fetchNotesForSubmission = submissionID => {
    return async function(dispatch) {
        dispatch(startFetchingNotes());
        try {
            const response = await api.fetchNotesForSubmission(submissionID);
            const json = await response.json();
            if (!response.ok) {
                return dispatch(failFetchingNotes(json.detail));
            }
            return dispatch(updateNotesForSubmission(submissionID, json));
        } catch(e) {
            return dispatch(failFetchingNotes(e.message));
        }
    };
};

const updateNotesForSubmission = (submissionID, data) => {
    return function(dispatch) {
        dispatch(updateNotes(data));
        dispatch(updateSubmission(submissionID, {
            comments: data.results.map(v => v.id),
        }));
    };
};

export const updateNotes = data => ({
    type: UPDATE_NOTES,
    data,
});

const startCreatingNoteForSubmission = submissionID => ({
    type: START_CREATING_NOTE_FOR_SUBMISSION,
    submissionID
});

const failCreatingNoteForSubmission = (submissionID, error) => ({
    type: FAIL_CREATING_NOTE_FOR_SUBMISSION,
    submissionID,
    error
});

const updateNote = (data, submissionID) => ({
    type: UPDATE_NOTE,
    submissionID,
    data,
});

const createdNoteForSubmission = (submissionID, data) => {
    return function(dispatch) {
        dispatch(updateNote(data, submissionID));
        dispatch(appendNoteIDForSubmission(submissionID, data.id));
        return true;
    };
};

export const createNoteForSubmission = (submissionID, note) => {
    return async function(dispatch) {
        dispatch(startCreatingNoteForSubmission(submissionID));
        try {
            const response = await api.createNoteForSubmission(submissionID, note);
            const json = await response.json();
            if (!response.ok) {
                return dispatch(failCreatingNoteForSubmission(
                    submissionID,
                    JSON.stringify(json)
                ));
            }
            return dispatch(createdNoteForSubmission(submissionID, json));
        } catch (e) {
            console.error(e);
            return dispatch(failCreatingNoteForSubmission(submissionID, e.message));
        }
    }
};
