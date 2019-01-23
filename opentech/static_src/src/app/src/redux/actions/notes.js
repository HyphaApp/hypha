import { updateSubmission } from '@actions/submissions';
import api from '@api';

export const FAIL_FETCHING_NOTES = 'FAIL_FETCHING_NOTES';
export const START_FETCHING_NOTES = 'START_FETCHING_NOTES';
export const UPDATE_NOTES = 'UPDATE_NOTES';
export const UPDATE_NOTE = 'UPDATE_NOTE';

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


export const createNoteForSubmission = (submissionID, note) => {
    return async function(dispatch) {
        try {
            const response = await api.createNoteForSubmission(submissionID, note);
            const json = await response.json();
            if (!response.ok) {
                console.error(json);
                return;
            }
            return;
        } catch (e) {
            console.error(e);
            return;
        }
    }
}
