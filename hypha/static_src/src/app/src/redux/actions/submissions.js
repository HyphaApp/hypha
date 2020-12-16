import { push } from 'connected-react-router'
import { CALL_API } from '@middleware/api'

import api from '@api';
import {
    getCurrentSubmission,
    getCurrentSubmissionID,
    getCurrentStatusesSubmissions
} from '@selectors/submissions';

import {
    getCurrentStatuses,
    getSubmissionIDsForCurrentStatuses,
} from '@selectors/statuses';

import {
    getRounds,
    getCurrentRoundID,
    getCurrentRound,
    getCurrentRoundSubmissionIDs,
} from '@selectors/rounds';

import {
    MESSAGE_TYPES,
    addMessage,
} from '@actions/messages';

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
export const SET_CURRENT_STATUSES = "SET_CURRENT_STATUSES_FOR_SUBMISSIONS";
export const UPDATE_BY_STATUSES = 'UPDATE_SUBMISSIONS_BY_STATUSES';
export const START_LOADING_BY_STATUSES = 'START_LOADING_SUBMISSIONS_BY_STATUSES';
export const FAIL_LOADING_BY_STATUSES = 'FAIL_LOADING_SUBMISSIONS_BY_STATUSES';

// Submissions
export const SET_CURRENT_SUBMISSION = 'SET_CURRENT_SUBMISSION';
export const START_LOADING_SUBMISSION = 'START_LOADING_SUBMISSION';
export const FAIL_LOADING_SUBMISSION = 'FAIL_LOADING_SUBMISSION';
export const UPDATE_SUBMISSION = 'UPDATE_SUBMISSION';
export const CLEAR_CURRENT_SUBMISSION = 'CLEAR_CURRENT_SUBMISSION';

// Execute submission action
export const START_EXECUTING_SUBMISSION_ACTION = 'START_EXECUTING_SUBMISSION_ACTION';
export const FAIL_EXECUTING_SUBMISSION_ACTION = 'FAIL_EXECUTING_SUBMISSION_ACTION';

// Notes
export const ADD_NOTE_FOR_SUBMISSION = 'ADD_NOTE_FOR_SUBMISSION';

// Review
export const TOGGLE_REVIEW_FORM = 'TOGGLE_REVIEW_FORM';
export const SET_CURRENT_REVIEW = 'SET_CURRENT_REVIEW';
export const CLEAR_CURRENT_REVIEW = 'CLEAR_CURRENT_REVIEW';
export const FETCH_REVIEW_DRAFT = 'FETCH_REVIEW_DRAFT';
export const CLEAR_REVIEW_DRAFT = 'CLEAR_REVIEW_DRAFT';

// Determination
export const TOGGLE_DETERMINATION_FORM = 'TOGGLE_DETERMINATION_FORM';
export const SET_CURRENT_DETERMINATION = 'SET_CURRENT_DETERMINATION';
export const CLEAR_CURRENT_DETERMINATION = 'CLEAR_CURRENT_DETERMINATION';
export const FETCH_DETERMINATION_DRAFT = 'FETCH_DETERMINATION_DRAFT';
export const CLEAR_DETERMINATION_DRAFT = 'CLEAR_DETERMINATION_DRAFT';


export const fetchDeterminationDraft = (submissionID) => ({
    [CALL_API]: {
        types: [ START_LOADING_SUBMISSION, FETCH_DETERMINATION_DRAFT, FAIL_LOADING_SUBMISSION],
        endpoint: api.fetchDeterminationDraft(submissionID),
    },
    submissionID,
})

export const clearDeterminationDraftAction = () => ({
    type: CLEAR_DETERMINATION_DRAFT,
});

export const toggleDeterminationFormAction = (status) =>({
    type : TOGGLE_DETERMINATION_FORM,
    status
});

export const setCurrentDeterminationAction = (determinationId) =>({
    type : SET_CURRENT_DETERMINATION,
    determinationId
});

export const clearCurrentDeterminationAction = () => ({
    type: CLEAR_CURRENT_DETERMINATION,
});

export const fetchReviewDraft = (submissionID) => ({
    [CALL_API]: {
        types: [ START_LOADING_SUBMISSION, FETCH_REVIEW_DRAFT, CLEAR_REVIEW_DRAFT],
        endpoint: api.fetchReviewDraft(submissionID),
    },
    submissionID,
})

export const clearReviewDraftAction = () => ({
    type: CLEAR_REVIEW_DRAFT,
});

export const toggleReviewFormAction = (status) =>({
    type : TOGGLE_REVIEW_FORM,
    status
});

export const setCurrentReviewAction = (reviewId) =>({
    type : SET_CURRENT_REVIEW,
    reviewId
});

export const clearCurrentReviewAction = () => ({
    type: CLEAR_CURRENT_REVIEW,
});

export const setCurrentSubmissionRound = (id) => (dispatch) => {
    dispatch({
        type: SET_CURRENT_SUBMISSION_ROUND,
        id,
    });

    return dispatch(loadCurrentRoundSubmissions());
};


export const loadSubmissionFromURL = (params) => (dispatch, getState) => {
    const urlParams = new URLSearchParams(params);
    if (urlParams.has('submission')) {
        const activeId = Number(urlParams.get('submission'));
        const submissionID = getCurrentSubmissionID(getState());

        if (activeId !== null  && submissionID !== activeId) {
            dispatch(setCurrentSubmission(activeId));
        }
        return true;
    }
    return false;
};



export const clearCurrentSubmissionParam = () => (dispatch, getState) => {
    const state = getState();
    if (state.router.location.search !== '') {
        return dispatch(push({search: ''}));
    }
};


const setSubmissionParam = (id) => (dispatch, getState) => {
    const state = getState();
    const submissionID = getCurrentSubmissionID(state);

    const urlParams = new URLSearchParams(state.router.location.search);
    const urlID = Number(urlParams.get('submission'));

    const shouldSet = !urlID && !!id;
    const shouldUpdate = id !== null  && submissionID !== id && urlID !== id;

    if (shouldSet || shouldUpdate) {
        dispatch(push({search: `?submission=${id}`}));
    } else if (id === null) {
        dispatch(clearCurrentSubmissionParam());
    }

};


export const setCurrentSubmissionParam = () => (dispatch, getState) => {
    const submissionID = getCurrentSubmissionID(getState());
    return dispatch(setSubmissionParam(submissionID));
};



export const setCurrentSubmission = id => (dispatch, getState) => {
    dispatch(toggleReviewFormAction(false))
    dispatch(clearCurrentReviewAction())
    dispatch(clearReviewDraftAction())
    dispatch(toggleDeterminationFormAction(false))
    dispatch(clearCurrentDeterminationAction())
    dispatch(clearDeterminationDraftAction())
    dispatch(setSubmissionParam(id));

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
        const currentSubmissionID = getCurrentSubmissionID(state)
        if (currentSubmissionID !== null &&  !ids.includes(currentSubmissionID)) {
            dispatch(addMessage('The selected submission is not available in this view', MESSAGE_TYPES.WARNING))
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


export const setCurrentStatuses = (statuses) => (dispatch) => {
    if(!Array.isArray(statuses)) {
        throw new Error("Statuses have to be an array of statuses");
    }

    dispatch({
        type: SET_CURRENT_STATUSES, 
        statuses,
    });

    return dispatch(loadSubmissionsForCurrentStatus());
};


const fetchSubmissionsByStatuses = (statuses) => {
    return {
        [CALL_API]: {
            types: [ START_LOADING_BY_STATUSES, UPDATE_BY_STATUSES, FAIL_LOADING_BY_STATUSES],
            endpoint: api.fetchSubmissionsByStatuses(statuses),
        },
        statuses,
    };
};

export const loadSubmissionsForCurrentStatus = () => (dispatch, getState) => {
    const state = getState()
    const submissions = getCurrentStatusesSubmissions(state)

    if ( submissions && submissions.length !== 0 ) {
        return null
    }

    return dispatch(fetchSubmissionsByStatuses(getCurrentStatuses(state))).then(() => {
        const state = getState()
        const ids = getSubmissionIDsForCurrentStatuses(state)
        const currentSubmissionID = getCurrentSubmissionID(state)
        if (currentSubmissionID !== null &&  !ids.includes(currentSubmissionID)) {
            dispatch(addMessage('The selected submission is not available in this view', MESSAGE_TYPES.WARNING))
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

export const loadCurrentSubmission = (requiredFields=[], { bypassCache = false }) => (dispatch, getState) => {
    const submissionID = getCurrentSubmissionID(getState())
    if ( !submissionID ) {
        return null
    }
    const submission = getCurrentSubmission(getState())

    if (!bypassCache && submission && requiredFields.every(key => submission.hasOwnProperty(key))) {
        return null
    }
    dispatch(fetchSubmission(submissionID))
    dispatch(fetchReviewDraft(submissionID))
    return dispatch(fetchDeterminationDraft(submissionID))
}


export const clearCurrentSubmission = () => ({
    type: CLEAR_CURRENT_SUBMISSION,
});

export const appendNoteIDForSubmission = (submissionID, noteID) => ({
    type: ADD_NOTE_FOR_SUBMISSION,
    submissionID,
    noteID,
});

export const executeSubmissionAction = (submissionID, action) => ({
    [CALL_API]: {
        types: [
            START_EXECUTING_SUBMISSION_ACTION,
            UPDATE_SUBMISSION,
            FAIL_EXECUTING_SUBMISSION_ACTION
        ],
        endpoint: api.executeSubmissionAction(submissionID, action),
    },
    submissionID,
    changedLocally: true,
})
