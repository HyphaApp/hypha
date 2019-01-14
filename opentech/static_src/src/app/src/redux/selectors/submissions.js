import { createSelector } from 'reselect';

const getSubmissionsByRound = state => state.submissions.itemsByRound;

const getCurrentRound = state => state.submissions.currentRound;

const getCurrentRoundSubmissions = createSelector(
  [ getSubmissionsByRound, getCurrentRound ],
  (submissionsByRound, currentRound) => submissionsByRound[currentRound] || []
);

const getCurrentRoundSubmissionsByStatus = createSelector(
    [getCurrentRoundSubmissions] ,
    currentRoundSubmissions => {
        const submissionsByStatus = {};
        for (const submission of currentRoundSubmissions) {
            if (!(submission.status in submissionsByStatus)) {
                submissionsByStatus[submission.status] = [];
            }
            submissionsByStatus[submission.status].push(submission);
        }
        const formattedSubmissionsByStatus = [];
        for (const [submissionStatus, statusSubmissions] of Object.entries(submissionsByStatus)) {
            formattedSubmissionsByStatus.push({
                id: submissionStatus,
                title: submissionStatus,
                submissions: statusSubmissions,
            });
        }
        return formattedSubmissionsByStatus;
    }
);

export {
    getCurrentRound,
    getCurrentRoundSubmissions,
    getCurrentRoundSubmissionsByStatus,
};
