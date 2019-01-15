import { createSelector } from 'reselect';

const getSubmissions = state => state.submissions.items;

const getSubmissionIDsByRound = state => state.submissions.itemsByRound;

const getCurrentRound = state => state.submissions.currentRound;


const getCurrentRoundSubmissions = createSelector(
    [ getSubmissionIDsByRound, getCurrentRound , getSubmissions],
    (submissionsByRound, currentRound, submissions) => {
        return (submissionsByRound[currentRound] || []).map(v => submissions[v])
    }
);

const getSubmissionsByRoundErrorState = state => state.submissions.itemsByRoundLoadingError;

const getSubmissionsByRoundLoadingState = state => state.submissions.itemsByRoundLoading;

export {
    getCurrentRound,
    getCurrentRoundSubmissions,
    getSubmissionsByRoundErrorState,
    getSubmissionsByRoundLoadingState,
};
