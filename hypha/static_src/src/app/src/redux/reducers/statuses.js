import { combineReducers } from 'redux';

import {
    SET_CURRENT_STATUSES,
    UPDATE_BY_STATUSES,
    START_LOADING_BY_STATUSES,
    FAIL_LOADING_BY_STATUSES,
    UPDATE_SUBMISSION,
} from '@actions/submissions';


function current(state = [], action) {
    switch (action.type) {
        case SET_CURRENT_STATUSES:
            return [...action.statuses]
        default:
            return state
    }
}

function submissionsByStatuses(state = {}, action) {
    switch (action.type) {
        case UPDATE_BY_STATUSES:
            return {
                ...state,
                ...action.data.results.reduce((accumulator, submission) => {
                    const submissions = accumulator[submission.status] || []
                    if ( !submissions.includes(submission.id) ) {
                        accumulator[submission.status] = [...submissions, submission.id]
                    }
                    return accumulator
                }, state)
            };
        case UPDATE_SUBMISSION:
            state = Object.entries(state).reduce(
                (accumulator, [status, ids]) => {
                    accumulator[status] = ids.filter(id => id !== action.data.id);
                    return accumulator;
                }, {});
            return {
                ...state,
                [action.data.status]: [...(state[action.data.status] || []), action.data.id],
            };
        default:
            return state
    }
}


function statusFetchingState(state = {isFetching: false, isError: false}, action) {
    switch (action.type) {
        case FAIL_LOADING_BY_STATUSES:
            return {
                isFetching: false,
                isErrored: true,
            };
        case START_LOADING_BY_STATUSES:
            return {
                isFetching: true,
                isErrored: false,
            };
        case UPDATE_BY_STATUSES:
            return {
                isFetching: false,
                isErrored: false,
            };
        default:
            return state
    }
}

const statuses = combineReducers({
    current,
    byStatuses: submissionsByStatuses,
    fetchingState: statusFetchingState,
});

export default statuses;
