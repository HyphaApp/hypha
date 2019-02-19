import { push } from 'connected-react-router'
import { CALL_API } from '@middleware/api'

import api from '@api';
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
    getCurrentRoundID,
    getCurrentRound,
    getCurrentRoundSubmissionIDs,
    getRounds,
    getSubmissionsByGivenStatuses,
} from '@selectors/submissions';


// Round
export const UPDATE_ROUND = 'UPDATE_ROUND';
export const START_LOADING_ROUND = 'START_LOADING_ROUND';
export const FAIL_LOADING_ROUND = 'FAIL_LOADING_ROUND';


// Rounds
export const UPDATE_ROUNDS = 'UPDATE_ROUNDS';
export const START_LOADING_ROUNDS = 'START_LOADING_ROUNDS';
export const FAIL_LOADING_ROUNDS = 'FAIL_LOADING_ROUNDS';

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


export const loadSubmissionFromURL = () => (dispatch, getState) => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('submission')) {
        const activeId = Number(urlParams.get('submission'));
        return dispatch(setCurrentSubmission(activeId));
    }
    return null;
}


export const setCurrentSubmission = id => (dispatch, getState) => {
    const submissionID = getCurrentSubmissionID(getState())

    if (id && submissionID !== id) {
        dispatch(push(`?submission=${id}`));
    } else if (!id) {
        dispatch(push('?'));
    }

    return dispatch({
        type: SET_CURRENT_SUBMISSION,
        id,
    })
};


export const loadCurrentRound = (requiredFields=[]) => (dispatch, getState) => {
    const state = getState()
    const round = getCurrentRound(state)

    if ( round && requiredFields.every(key => round.hasOwnProperty(key)) ) {
        return null
    }

    return dispatch(fetchRound(getCurrentRoundID(state)))
}


export const loadRounds = () => (dispatch, getState) => {
    const state = getState()
    const rounds = getRounds(state)

    if ( rounds && Object.keys(rounds).length !== 0 ) {
        return null
    }
    return dispatch(fetchRounds())
}


export const loadCurrentRoundSubmissions = () => (dispatch, getState) => {
    const state = getState()
    const submissions = getCurrentRoundSubmissionIDs(state)

    if ( submissions && submissions.length !== 0 ) {
        return null
    }

    return dispatch(fetchSubmissionsByRound(getCurrentRoundID(state))).then(() => {
        const state = getState()
        const ids = getCurrentRoundSubmissionIDs(state)
        if (!ids.includes(getCurrentSubmissionID(state))) {
            return dispatch(setCurrentSubmission(null))
        }
    })
}


const fetchRound = (roundID) => ({
    [CALL_API]: {
        types: [ START_LOADING_ROUND, UPDATE_ROUND, FAIL_LOADING_ROUND],
        endpoint: api.fetchRound(roundID),
    },
    roundID,
})


const fetchRounds = () => ({
    [CALL_API]: {
        types: [ START_LOADING_ROUNDS, UPDATE_ROUNDS, FAIL_LOADING_ROUNDS],
        endpoint: api.fetchRounds(),
    },
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
    const state = getState()
    const submissions = getSubmissionsByGivenStatuses(statuses)(state)

    if ( submissions && submissions.length !== 0 ) {
        return null
    }

    return dispatch(fetchSubmissionsByStatuses(statuses)).then(() => {
        const state = getState()
        const ids = getSubmissionsByGivenStatuses(statuses)(state)
        if (!ids.includes(getCurrentSubmissionID(state))) {
            return dispatch(setCurrentSubmission(null))
        }
    })
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
