import { createSelector } from 'reselect';

const getSubmissions = state => state.submissions.byID;

const getRounds = state => state.rounds.byID;

const getCurrentRoundID = state => state.rounds.current;

const getCurrentRound = createSelector(
    [ getCurrentRoundID, getRounds],
    (id, rounds) => {
        return rounds[id];
    }
);

const getCurrentSubmissionID = state => state.submissions.current;


const getCurrentRoundSubmissions = createSelector(
    [ getCurrentRound, getSubmissions],
    (round, submissions) => {
        const roundSubmissions = round ? round.submissions : [];
        return roundSubmissions.map(submissionID => submissions[submissionID]);
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

const getSubmissionsByRoundError = state => state.rounds.error;

const getSubmissionsByRoundLoadingState = state => state.submissions.itemsLoading === true;

export {
    getCurrentRoundID,
    getCurrentRound,
    getCurrentRoundSubmissions,
    getCurrentSubmission,
    getCurrentSubmissionID,
    getSubmissionsByRoundError,
    getSubmissionsByRoundLoadingState,
    getSubmissionLoadingState,
    getSubmissionErrorState,
};
