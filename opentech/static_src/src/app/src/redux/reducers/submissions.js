import {
    FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    SET_CURRENT_SUBMISSION_ROUND,
    START_LOADING_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSIONS_BY_ROUND,
} from '@actions/submissions';

const initialState = {
    currentRound: null,
    items: {},
    itemsByRound: {},
    itemsByRoundLoadingError: false,
    itemsByRoundLoading: false,
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
                items: {
                    ...state.items,
                    ...action.data.results.reduce((newItems, v) => {
                        newItems[v.id] = { ...v };
                        return newItems;
                    }, {}),
                },
                itemsByRound: {
                    ...state.itemsByRound,
                    [action.roundId]: action.data.results.map(v => v.id),
                },
                itemsByRoundLoading: false,
                itemsByRoundLoadingError: false,
            };
        case FAIL_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                itemsByRoundLoading: false,
                itemsByRoundLoadingError: true,
            };
        case START_LOADING_SUBMISSIONS_BY_ROUND:
            return {
                ...state,
                itemsByRoundLoading: true,
                itemsByRoundLoadingError: false,
            };
        default:
            return state;
    }
}
