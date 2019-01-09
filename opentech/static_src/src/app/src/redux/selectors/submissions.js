import { createSelector } from 'reselect';

const getSubmissionsByRound = (state) => state.submissions.itemsByRound;

const getCurrentRound = (state) => state.submissions.currentRound;

const getCurrentRoundSubmissions = createSelector(
  [ getSubmissionsByRound, getCurrentRound ],
  (submissionsByRound, currentRound) => submissionsByRound[currentRound] || []
);

export {
    getCurrentRoundSubmissions,
};
