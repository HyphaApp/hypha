import {
    FAIL_LOADING_SUBMISSION,
    START_LOADING_SUBMISSION,
    UPDATE_SUBMISSION,
    FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    SET_CURRENT_SUBMISSION,
    SET_CURRENT_SUBMISSION_ROUND,
    START_LOADING_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSIONS_BY_ROUND,
} from '@actions/submissions';

const initialState = {
    currentRound: null,
    currenSubmission: null,
    submissionsByID: {},
    submissionsByRoundID: {},
    itemsLoadingError: false,
    itemsLoading: false,
    itemLoading: false,
    itemLoadingError: false,
};

export default function submissions(state = initialState, action) {
    switch(action.type) {
        // Submissions by round
        case SET_CURRENT_SUBMISSION:
            return {
                ...state,
                currentSubmission: action.id,
            };
        case SET_CURRENT_SUBMISSION_ROUND:
            return {
                ...state,
                currentRound: action.id,
            };
        case UPDATE_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                submissionsByID: {
                    ...state.submissionsByID,
                    ...action.data.results.reduce((newItems, v) => {
                        newItems[v.id] = {
                            ...state.submissionsByID[v.id],
                            ...v
                        };
                        return newItems;
                    }, {}),
                },
                submissionsByRoundID: {
                    ...state.submissionsByRoundID,
                    [action.roundId]: action.data.results.map(v => v.id),
                },
                itemsLoading: false,
                itemsLoadingError: false,
            };
        case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                itemsLoading: false,
                itemsLoadingError: true,
            };
        case START_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                itemsLoading: true,
                itemsLoadingError: false,
            };

        // Submission
        case START_LOADING_SUBMISSION:
            return {
                ...state,
                itemLoading: true,
                itemLoadingError: false,
            };
        case FAIL_LOADING_SUBMISSION:
            return {
                ...state,
                itemLoading: false,
                itemLoadingError: true,
            };
        case UPDATE_SUBMISSION:
            return {
                ...state,
                submissionsByID: {
                    ...state.submissionsByID,
                    [action.submissionID]: {
                        ...state.submissionsByID[action.submissionID],
                        ...action.data,
                    }
                },
                itemLoading: false,
                itemLoadingError: false,
            };
        case CLEAR_CURRENT_SUBMISSION:
            return {
                ...state,
                currentSubmission: null,
            }
        default:
            return state;
    }
}
