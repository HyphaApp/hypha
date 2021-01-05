import { combineReducers } from 'redux';

import {
    CLEAR_CURRENT_SUBMISSION,
    FAIL_LOADING_SUBMISSION,
    START_LOADING_SUBMISSION,
    UPDATE_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSION,
    SET_CURRENT_SUBMISSION,
    UPDATE_BY_STATUSES,
    START_EXECUTING_SUBMISSION_ACTION,
    FAIL_EXECUTING_SUBMISSION_ACTION,
    TOGGLE_REVIEW_FORM,
    SET_CURRENT_REVIEW,
    CLEAR_CURRENT_REVIEW,
    FETCH_REVIEW_DRAFT,
    CLEAR_REVIEW_DRAFT,
    TOGGLE_DETERMINATION_FORM,
    SET_CURRENT_DETERMINATION,
    CLEAR_CURRENT_DETERMINATION,
    FETCH_DETERMINATION_DRAFT,
    CLEAR_DETERMINATION_DRAFT,
    CLEAR_ALL_SUBMISSIONS
} from '@actions/submissions';

import { CREATE_NOTE, UPDATE_NOTES, UPDATE_NOTE } from '@actions/notes'


function submission(state={comments: []}, action) {
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
                isExecutingAction: false,
                isExecutingActionErrored: false,
                executionActionError: undefined,
                changedLocally: action.changedLocally === true
            };
        case UPDATE_NOTES:
            return {
                ...state,
                comments: action.data.results
                    .map(note => note.id)
                    .filter(id => !state.comments.includes(id))
                    .concat(state.comments)
            };
        case START_EXECUTING_SUBMISSION_ACTION:
            return {
                ...state,
                isExecutingAction: true,
                isExecutingActionErrored: false,
                executionActionError: undefined,
            };
        case FAIL_EXECUTING_SUBMISSION_ACTION:
            return {
                ...state,
                isExecutingAction: false,
                isExecutingActionErrored: true,
                executionActionError: action.error
            };
        case UPDATE_NOTE:
            return {
                ...state,
                comments: [
                    action.data.id,
                    ...(state.comments.filter(comment => comment !== action.note.id) || []),
                ]
            };
        case CREATE_NOTE:
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
        case CREATE_NOTE:
        case UPDATE_NOTE:
        case UPDATE_NOTES:
        case START_EXECUTING_SUBMISSION_ACTION:
        case FAIL_EXECUTING_SUBMISSION_ACTION:
            return {
                ...state,
                [action.submissionID]: submission(state[action.submissionID], action),
            };
        case UPDATE_BY_STATUSES:
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
        case CLEAR_ALL_SUBMISSIONS:
            return {}
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
        case CLEAR_ALL_SUBMISSIONS:
                return null;
        default:
            return state;
    }
}

function toggleReviewForm(state= false, action){
    switch(action.type){
        case TOGGLE_REVIEW_FORM:
            return action.status
        default:
            return state
    }
}

function currentReview(state = null, action) {
    switch(action.type) {
        case SET_CURRENT_REVIEW:
            return action.reviewId;
        case CLEAR_CURRENT_REVIEW:
            return null;
        default:
            return state;
    }
}

function isReviewDraftExist(state = false, action) {
    switch(action.type) {
        case FETCH_REVIEW_DRAFT:
            return action.data.isDraft ? true : false;
        case CLEAR_REVIEW_DRAFT:
            return false;
        default:
            return state;
    }
}

function toggleDeterminationForm(state= false, action){
    switch(action.type){
        case TOGGLE_DETERMINATION_FORM:
            return action.status
        default:
            return state
    }
}

function currentDetermination(state = null, action) {
    switch(action.type) {
        case SET_CURRENT_DETERMINATION:
            return action.determinationId;
        case CLEAR_CURRENT_DETERMINATION:
            return null;
        default:
            return state;
    }
}

function isDeterminationDraftExist(state = false, action) {
    switch(action.type) {
        case FETCH_DETERMINATION_DRAFT:
            return action.data.isDraft ? true : false;
        case CLEAR_DETERMINATION_DRAFT:
            return false;
        default:
            return state;
    }
}



const submissions = combineReducers({
    byID: submissionsByID,
    current: currentSubmission,
    showReviewForm : toggleReviewForm,
    currentReview,
    isReviewDraftExist,
    showDeterminationForm: toggleDeterminationForm,
    currentDetermination,
    isDeterminationDraftExist,
});

export default submissions;
