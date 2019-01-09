import { SET_CURRENT_SUBMISSION_ROUND, UPDATE_SUBMISSIONS_BY_ROUND } from '@actions/submissions';

const initialState = {
    currentRound: null,
    itemsByRound: {}
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
            };
        default:
            return state;
    }
}
