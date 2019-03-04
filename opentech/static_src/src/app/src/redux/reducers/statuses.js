import { combineReducers } from 'redux';

import {
    SET_CURRENT_STATUSES,
    UPDATE_BY_STATUSES,
    START_LOADING_BY_STATUSES,
    FAIL_LOADING_BY_STATUSES,
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
        default:
            return state
    }
}


function statusFetchingState(state = {isFetching: true, isError: false}, action) {
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
