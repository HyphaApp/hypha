import { combineReducers } from 'redux';

import {
    FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    SET_CURRENT_SUBMISSION_ROUND,
    START_LOADING_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSIONS_BY_ROUND,
    FAIL_LOADING_ROUND,
    START_LOADING_ROUND,
    UPDATE_ROUND,
    UPDATE_ROUNDS,
    FAIL_LOADING_ROUNDS,
    START_LOADING_ROUNDS,
} from '@actions/submissions';

const submissionsDefaultState = {ids: [], isFetching: false};

function submissions(state=submissionsDefaultState, action) {
    switch (action.type) {
        case UPDATE_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                ids: action.data.results.map(submission => submission.id),
                isFetching: false,
            };
        case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                isFetching: false,
            };
        case START_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                isFetching: true,
            };
        default:
            return state;
    }
}


function round(state={id: null, submissions: submissionsDefaultState, isFetching: false, workflow: []}, action) {
    switch(action.type) {
        case UPDATE_SUBMISSIONS_BY_ROUND:
        case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
        case START_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                id: action.roundID,
                submissions: submissions(state.submissions, action),
            };
        case UPDATE_ROUND:
            return {
                ...state,
                ...action.data,
                isFetching: false,
            };
        case FAIL_LOADING_ROUND:
            return {
                ...state,
                isFetching: false,
            };
        case START_LOADING_ROUND:
            return {
                ...state,
                id: action.roundID,
                isFetching: true,
            };
        default:
            return state;
    }
}


function roundsByID(state = {}, action) {
    switch(action.type) {
        case UPDATE_SUBMISSIONS_BY_ROUND:
        case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
        case START_LOADING_SUBMISSIONS_BY_ROUND:
        case UPDATE_ROUND:
        case START_LOADING_ROUND:
        case FAIL_LOADING_ROUND:
            return {
                ...state,
                [action.roundID]: round(state[action.roundID], action)
            };
        case UPDATE_ROUNDS:
            return {
                ...state,
                ...action.data.results.reduce((acc, value) => {
                    acc[value.id] = round(state[value.id], {
                        type: UPDATE_ROUND,
                        data: value
                    });
                    return acc;
                }, {}),
            };
        default:
            return state;
    }
}


function errorMessage(state = null, action) {
    switch(action.type) {
    case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
    case FAIL_LOADING_ROUND:
        return action.message;
    case UPDATE_SUBMISSIONS_BY_ROUND:
    case START_LOADING_SUBMISSIONS_BY_ROUND:
    case UPDATE_ROUND:
    case START_LOADING_ROUND:
        return null;
    default:
        return state;
    }

}

function roundsErrored(state = false, action) {
    switch (action.type) {
        case START_LOADING_ROUNDS:
        case UPDATE_ROUNDS:
            return false;
        case FAIL_LOADING_ROUNDS:
            return true;
        default:
            return state;
    }
}

function roundsFetching(state = false, action) {
    switch (action.type) {
        case FAIL_LOADING_ROUNDS:
        case UPDATE_ROUNDS:
            return false;
        case START_LOADING_ROUNDS:
            return true;
        default:
            return state;
    }
}


function currentRound(state = null, action) {
    switch(action.type) {
        case SET_CURRENT_SUBMISSION_ROUND:
            return action.id;
        default:
            return state;
    }
}


const rounds = combineReducers({
    byID: roundsByID,
    current: currentRound,
    error: errorMessage,
    isFetching: roundsFetching,
    isErrored: roundsErrored,
});

export default rounds;
