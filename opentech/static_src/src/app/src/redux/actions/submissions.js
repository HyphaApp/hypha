import api from '@api';
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
    getCurrentRoundID,
    getCurrentRound,
    getCurrentRoundSubmissionIDs,
} from '@selectors/submissions';


// Round
export const UPDATE_ROUND = 'UPDATE_ROUND';
export const START_LOADING_ROUND = 'START_LOADING_ROUND';
export const FAIL_LOADING_ROUND = 'FAIL_LOADING_ROUND';

// Submissions by round
export const SET_CURRENT_SUBMISSION_ROUND = 'SET_CURRENT_SUBMISSION_ROUND';
export const UPDATE_SUBMISSIONS_BY_ROUND = 'UPDATE_SUBMISSIONS_BY_ROUND';
export const START_LOADING_SUBMISSIONS_BY_ROUND = 'START_LOADING_SUBMISSIONS_BY_ROUND';
export const FAIL_LOADING_SUBMISSIONS_BY_ROUND = 'FAIL_LOADING_SUBMISSIONS_BY_ROUND';

// Submissions
export const SET_CURRENT_SUBMISSION = 'SET_CURRENT_SUBMISSION';
export const START_LOADING_SUBMISSION = 'START_LOADING_SUBMISSION';
export const FAIL_LOADING_SUBMISSION = 'FAIL_LOADING_SUBMISSION';
export const UPDATE_SUBMISSION = 'UPDATE_SUBMISSION';
export const CLEAR_CURRENT_SUBMISSION = 'CLEAR_CURRENT_SUBMISSION';

// Notes
export const ADD_NOTE_FOR_SUBMISSION = 'ADD_NOTE_FOR_SUBMISSION';

export const setCurrentSubmissionRound = id => ({
    type: SET_CURRENT_SUBMISSION_ROUND,
    id,
});

export const setCurrentSubmission = id => ({
    type: SET_CURRENT_SUBMISSION,
    id,
});


export const loadCurrentRound = (requiredFields=[]) => (dispatch, getState) => {
    const state = getState()
    const round = getCurrentRound(state)

    if ( round && requiredFields.every(key => round.hasOwnProperty(key)) ) {
        return null
    }

    return dispatch(fetchRound(getCurrentRoundID(state)))
}

export const loadCurrentRoundSubmissions = () => (dispatch, getState) => {
    const state = getState()
    const submissions = getCurrentRoundSubmissionIDs(state)

    if ( submissions && submissions.length !== 0 ) {
        return null
    }

    return dispatch(fetchSubmissionsByRound(getCurrentRoundID(state)))
}


export const fetchRound = roundID => {
    return async function(dispatch) {
        dispatch(startLoadingRound(roundID));
        try {
            const response = await api.fetchRound(roundID);
            const json = await response.json();
            if (response.ok) {
                dispatch(updateRound(roundID, json));
            } else {
                dispatch(failLoadingRound(json.detail));
            }
        } catch (e) {
            dispatch(failLoadingRound(e.message));
        }
    };
};


const updateRound = (roundID, data) => ({
    type: UPDATE_ROUND,
    roundID,
    data,
});


const startLoadingRound = (roundID) => ({
    type: START_LOADING_ROUND,
    roundID,
});


const failLoadingRound = (message) => ({
    type: FAIL_LOADING_ROUND,
    message,
});



export const fetchSubmissionsByRound = roundID => {
    return async function(dispatch) {
        dispatch(startLoadingSubmissionsByRound(roundID));
        try {
            const response = await api.fetchSubmissionsByRound(roundID);
            const json = await response.json();
            if (response.ok) {
                dispatch(updateSubmissionsByRound(roundID, json));
            } else {
                dispatch(failLoadingSubmissionsByRound(json.detail));
            }
        } catch (e) {
            dispatch(failLoadingSubmissionsByRound(e.message));
        }
    };
};


const updateSubmissionsByRound = (roundID, data) => ({
    type: UPDATE_SUBMISSIONS_BY_ROUND,
    roundID,
    data,
});


const startLoadingSubmissionsByRound = (roundID) => ({
    type: START_LOADING_SUBMISSIONS_BY_ROUND,
    roundID,
});


const failLoadingSubmissionsByRound = (message) => ({
    type: FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    message,
});


export const loadCurrentSubmission = (requiredFields=[]) => (dispatch, getState) => {
    const submissionID = getCurrentSubmissionID(getState())
    if ( !submissionID ) {
        return null
    }
    const submission = getCurrentSubmission(getState())

    if (submission && requiredFields.every(key => submission.hasOwnProperty(key))) {
        return null
    }

    return dispatch(fetchSubmission(submissionID))
}


export const fetchSubmission = submissionID => {
    return async function(dispatch) {

        dispatch(startLoadingSubmission(submissionID));
        try {
            const response = await api.fetchSubmission(submissionID);
            const json = await response.json();
            if (response.ok) {
                dispatch(updateSubmission(submissionID, json));
            } else {
                dispatch(failLoadingSubmission(json.detail));
            }
        } catch (e) {
            dispatch(failLoadingSubmission(e.message));
        }
    };
};


const startLoadingSubmission = submissionID => ({
    type: START_LOADING_SUBMISSION,
    submissionID,
});

const failLoadingSubmission = submissionID => ({
    type: FAIL_LOADING_SUBMISSION,
    submissionID,
});


export const updateSubmission = (submissionID, data) => ({
    type: UPDATE_SUBMISSION,
    submissionID,
    data,
});

export const clearCurrentSubmission = () => ({
    type: CLEAR_CURRENT_SUBMISSION,
});

export const appendNoteIDForSubmission = (submissionID, noteID) => ({
    type: ADD_NOTE_FOR_SUBMISSION,
    submissionID,
    noteID,
});
