import { CALL_API } from '@middleware/api'

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

// Submissions by statuses
export const UPDATE_SUBMISSIONS_BY_STATUSES = 'UPDATE_SUBMISSIONS_BY_STATUSES';
export const START_LOADING_SUBMISSIONS_BY_STATUSES = 'START_LOADING_SUBMISSIONS_BY_STATUSES';
export const FAIL_LOADING_SUBMISSIONS_BY_STATUSES = 'FAIL_LOADING_SUBMISSIONS_BY_STATUSES';

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


const fetchRound = (roundID) => ({
    [CALL_API]: {
        types: [ START_LOADING_ROUND, UPDATE_ROUND, FAIL_LOADING_ROUND],
        endpoint: api.fetchRound(roundID),
    },
    roundID,
})

const fetchSubmissionsByRound = (roundID) => ({
    [CALL_API]: {
        types: [ START_LOADING_SUBMISSIONS_BY_ROUND, UPDATE_SUBMISSIONS_BY_ROUND, FAIL_LOADING_SUBMISSIONS_BY_ROUND],
        endpoint: api.fetchSubmissionsByRound(roundID),
    },
    roundID,
})


const fetchSubmissionsByStatuses = statuses => {
    if(!Array.isArray(statuses)) {
        throw new Error("Statuses have to be an array of statuses");
    }

    return {
        [CALL_API]: {
            types: [ START_LOADING_SUBMISSIONS_BY_STATUSES, UPDATE_SUBMISSIONS_BY_STATUSES, FAIL_LOADING_SUBMISSIONS_BY_STATUSES],
            endpoint: api.fetchSubmissionsByStatuses(statuses),
        },
        statuses,
    };
};

export const loadSubmissionsOfStatuses = statuses => (dispatch, getState) => {
    //const state = getState()
    //const submissions = getCurrentRoundSubmissionIDs(state)

    //if ( submissions && submissions.length !== 0 ) {
        //return null
    //}

    return dispatch(fetchSubmissionsByStatuses(statuses))
}

const fetchSubmission = (submissionID) => ({
    [CALL_API]: {
        types: [ START_LOADING_SUBMISSION, UPDATE_SUBMISSION, FAIL_LOADING_SUBMISSION],
        endpoint: api.fetchSubmission(submissionID),
    },
    submissionID,
})

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


export const clearCurrentSubmission = () => ({
    type: CLEAR_CURRENT_SUBMISSION,
});

export const appendNoteIDForSubmission = (submissionID, noteID) => ({
    type: ADD_NOTE_FOR_SUBMISSION,
    submissionID,
    noteID,
});
