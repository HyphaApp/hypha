import { combineReducers } from 'redux';

import {
    FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    SET_CURRENT_SUBMISSION_ROUND,
    START_LOADING_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSIONS_BY_ROUND,
} from '@actions/submissions';


function round(state={id: null, submissions: [], isFetching: false}, action) {
    switch(action.type) {
        case UPDATE_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                id: action.roundID,
                submissions: action.data.results.map(submission => submission.id),
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
            return {
                ...state,
                [action.roundID]: round(state[action.roundID], action)
            };
        default:
            return state;
    }
}


function errorMessage(state = null, action) {
    switch(action.type) {
    case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
        return action.message;
    case UPDATE_SUBMISSIONS_BY_ROUND:
    case START_LOADING_SUBMISSIONS_BY_ROUND:
        return null;
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
});

export default rounds;
