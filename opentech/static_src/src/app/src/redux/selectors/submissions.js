import { createSelector } from 'reselect';

const getSubmissions = state => state.submissions.submissionsByID;

const getSubmissionIDsByRound = state => state.submissions.submissionsByRoundID;

const getCurrentRoundID = state => state.submissions.currentRound;

const getCurrentSubmissionID = state => state.submissions.currentSubmission;


const getCurrentRoundSubmissions = createSelector(
    [ getSubmissionIDsByRound, getCurrentRoundID , getSubmissions],
    (submissionsByRound, currentRoundID, submissions) => {
        return (submissionsByRound[currentRoundID] || []).map(submissionID => submissions[submissionID]);
    }
);

const getCurrentSubmission = createSelector(
    [ getCurrentSubmissionID, getSubmissions ],
    (id, submissions) => {
        return submissions[id];
    }
);

const getSubmissionLoadingState = state => state.submissions.itemLoading === true;

const getSubmissionErrorState = state => state.submissions.itemLoadingError === true;

const getSubmissionsByRoundErrorState = state => state.submissions.itemsLoadingError === true;

const getSubmissionsByRoundLoadingState = state => state.submissions.itemsLoading === true;

export {
    getCurrentRoundID,
    getCurrentRoundSubmissions,
    getCurrentSubmission,
    getCurrentSubmissionID,
    getSubmissionsByRoundErrorState,
    getSubmissionsByRoundLoadingState,
    getSubmissionLoadingState,
    getSubmissionErrorState,
};
