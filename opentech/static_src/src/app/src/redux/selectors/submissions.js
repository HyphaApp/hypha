import { createSelector } from 'reselect';

const getSubmissionsByRound = (state) => state.submissions.itemsByRound;

const getCurrentRound = (state) => state.submissions.currentRound;

const getCurrentRoundSubmissions = createSelector(
  [ getSubmissionsByRound, getCurrentRound ],
  (submissionsByRound, currentRound) => submissionsByRound[currentRound] || []
);

const getCurrentRoundSubmissionsByStatus = createSelector(
    [getCurrentRoundSubmissions] ,
    currentRoundSubmissions => {
        const submissionsByStatus = [{
            title: 'Test stage',
            applications: currentRoundSubmissions,
        }];
        return submissionsByStatus;
    }
);

export {
    getCurrentRoundSubmissions,
    getCurrentRoundSubmissionsByStatus,
};
