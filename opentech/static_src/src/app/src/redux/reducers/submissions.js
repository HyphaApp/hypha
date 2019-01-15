import {
    FAIL_LOADING_SUBMISSIONS_BY_ROUND,
    SET_CURRENT_SUBMISSION_ROUND,
    START_LOADING_SUBMISSIONS_BY_ROUND,
    UPDATE_SUBMISSIONS_BY_ROUND,
} from '@actions/submissions';

const initialState = {
    currentRound: null,
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
            const newData = {};
            newData[action.roundId] = action.data.results;

            return {
                ...state,
                itemsByRound: {
                    ...state.itemsByRound,
                    ...newData,
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
