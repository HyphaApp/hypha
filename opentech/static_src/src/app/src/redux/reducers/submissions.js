import {
    FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    SET_CURRENT_SUBMISSION_ROUND,
    START_LOADING_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSIONS_BY_ROUND,
} from '@actions/submissions';

const initialState = {
    currentRound: null,
    submissionsByID: {},
    submissionsByRoundID: {},
    itemsLoadingError: false,
    itemsLoading: false,
};

export default function submissions(state = initialState, action) {
    switch(action.type) {
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
        default:
            return state;
    }
}
