import { combineReducers } from 'redux';

import {
    CLEAR_CURRENT_SUBMISSION,
    FAIL_LOADING_SUBMISSION,
    START_LOADING_SUBMISSION,
    UPDATE_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSION,
    SET_CURRENT_SUBMISSION,
    UPDATE_SUBMISSIONS_BY_STATUSES,
} from '@actions/submissions';

import { UPDATE_NOTES, UPDATE_NOTE } from '@actions/notes'


function submission(state, action) {
    switch(action.type) {
        case START_LOADING_SUBMISSION:
            return {
                ...state,
                isFetching: true,
                isErrored: false,
            };
        case FAIL_LOADING_SUBMISSION:
            return {
                ...state,
                isFetching: false,
                isErrored: true,
            };
        case UPDATE_SUBMISSION:
            return {
                ...state,
                ...action.data,
                isFetching: false,
                isErrored: false,
            };
        case UPDATE_NOTES:
            return {
                ...state,
                comments: action.data.results.map(note => note.id),
            };
        case UPDATE_NOTE:
            return {
                ...state,
                comments: [
                    action.data.id,
                    ...(state.comments || []),
                ]
            };
        default:
            return state;
    }
}


function submissionsByID(state = {}, action) {
    switch(action.type) {
        case START_LOADING_SUBMISSION:
        case FAIL_LOADING_SUBMISSION:
        case UPDATE_SUBMISSION:
        case UPDATE_NOTE:
        case UPDATE_NOTES:
            return {
                ...state,
                [action.submissionID]: submission(state[action.submissionID], action),
            };
        case UPDATE_SUBMISSIONS_BY_STATUSES:
        case UPDATE_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                ...action.data.results.reduce((newItems, newSubmission) => {
                    newItems[newSubmission.id] = submission(
                        state[newSubmission.id],
                        {
                            type: UPDATE_SUBMISSION,
                            data: newSubmission,
                        }
                    );
                    return newItems;
                }, {}),
            };
        default:
            return state;
    }
}


function currentSubmission(state = null, action) {
    switch(action.type) {
        case SET_CURRENT_SUBMISSION:
            return action.id;
        case CLEAR_CURRENT_SUBMISSION:
            return null;
        default:
            return state;
    }
}


function submissionsByStatuses(state = {}, action) {
    switch (action.type) {
        case UPDATE_SUBMISSIONS_BY_STATUSES:
            return {
                ...state,
                [action.statuses]: action.data.results.map(v => v.id),
            };
        default:
            return state
    }
}


const submissions = combineReducers({
    byID: submissionsByID,
    current: currentSubmission,
    byStatuses: submissionsByStatuses,
});

export default submissions;
