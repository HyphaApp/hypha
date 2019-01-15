import { createSelector } from 'reselect';

const getSubmissions = state => state.submissions.submissionsByID;

const getSubmissionIDsByRound = state => state.submissions.submissionsByRoundID;

const getCurrentRoundID = state => state.submissions.currentRound;


const getCurrentRoundSubmissions = createSelector(
    [ getSubmissionIDsByRound, getCurrentRoundID , getSubmissions],
    (submissionsByRound, currentRoundID, submissions) => {
        return (submissionsByRound[currentRoundID] || []).map(submissionID => submissions[submissionID]);
    }
);

const getSubmissionsByRoundErrorState = state => state.submissions.itemsLoadingError;

const getSubmissionsByRoundLoadingState = state => state.submissions.itemsLoading;

export {
    getCurrentRoundID,
    getCurrentRoundSubmissions,
    getSubmissionsByRoundErrorState,
    getSubmissionsByRoundLoadingState,
};
