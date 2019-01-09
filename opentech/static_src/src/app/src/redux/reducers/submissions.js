import { SET_CURRENT_SUBMISSION_ROUND } from '@actions/submissions';

const initialState = {
    currentRound: null,
    itemsByRound: {
        796: [
            {
                title: "Test stage 1",
                applications: [],
            },
            {
                title: "Test stage 2 blabla",
                applications: [],
            },
        ]
    }
};

export default function submissions(state = initialState, action) {
    switch(action.type) {
        case SET_CURRENT_SUBMISSION_ROUND:
            return {
                ...state,
                currentRound: action.id,
            };
        default:
            return state;
    }
}
