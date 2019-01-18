import api from '@api';
import { getCurrentSubmissionID } from '@selectors/submissions';


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

export const setCurrentSubmissionRound = id => ({
    type: SET_CURRENT_SUBMISSION_ROUND,
    id,
});

export const setCurrentSubmission = id => {
    return dispatch => {
        dispatch({
            type: SET_CURRENT_SUBMISSION,
            id,
        });
        dispatch(fetchSubmission(id));
    };
};

export const fetchSubmissionsByRound = roundId => {
    return async function(dispatch) {
        dispatch(startLoadingSubmissionsByRound());
        try {
            const response = await api.fetchSubmissionsByRound(roundId);
            const json = await response.json();
            if (!response.ok) {
                dispatch(failLoadingSubmissionsByRound(submissionID, data));
                return;
            }
            dispatch(updateSubmissionsByRound(roundId, json));
        } catch (e) {
            console.error(e);
            dispatch(failLoadingSubmissionsByRound());
        }
    };
};


const updateSubmissionsByRound = (roundId, data) => ({
    type: UPDATE_SUBMISSIONS_BY_ROUND,
    roundId,
    data,
});


const startLoadingSubmissionsByRound = () => ({
    type: START_LOADING_SUBMISSIONS_BY_ROUND,
});



const failLoadingSubmissionsByRound = () => ({
    type: FAIL_LOADING_SUBMISSIONS_BY_ROUND,
});


export const fetchSubmission = submissionID => {
    return async function(dispatch) {

        dispatch(startLoadingSubmission());
        try {
            const response = await api.fetchSubmission(submissionID);
            const json = await response.json();
            if (!response.ok) {
                dispatch(failLoadingSubmission());
            }
            dispatch(updateSubmission(submissionID, json));
        } catch(e) {
            console.error(e);
            dispatch(failLoadingSubmission());
        }
    };
};

const startLoadingSubmission = () => ({
    type: START_LOADING_SUBMISSION,
});

const failLoadingSubmission = () => ({
    type: FAIL_LOADING_SUBMISSION,
});

const updateSubmission = (submissionID, data) => ({
    type: UPDATE_SUBMISSION,
    submissionID,
    data,
});

export const clearCurrentSubmission = () => ({
    type: CLEAR_CURRENT_SUBMISSION,
});
