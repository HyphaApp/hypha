import { createSelector } from 'reselect';

const getSubmissions = state => state.submissions.byID;

const getRounds = state => state.rounds.byID;

const getSubmissionsByStatuses = state => state.submissions.byStatuses;

const getCurrentRoundID = state => state.rounds.current;

const getCurrentRound = createSelector(
    [ getCurrentRoundID, getRounds],
    (id, rounds) => {
        return rounds[id];
    }
);

const getCurrentSubmissionID = state => state.submissions.current;

const getByGivenStatusesObject = statuses => createSelector(
    [getSubmissionsByStatuses], (byStatuses) => {
        for (const [key, value] of Object.entries(byStatuses)) {
            if (key.split(',').every(v => statuses.includes(v))) {
                return value;
            }
        }
        return {};
    }
);

const getSubmissionsByGivenStatuses = statuses => createSelector(
    [getSubmissions, getByGivenStatusesObject(statuses)],
    (submissions, byStatus) => (byStatus.ids || []).map(id => submissions[id])
);

const getByGivenStatusesError = statuses => createSelector(
    [getByGivenStatusesObject(statuses)],
    byStatus => byStatus.isErrored === true
);

const getByGivenStatusesLoading = statuses => createSelector(
    [getByGivenStatusesObject(statuses)],
    byStatus => byStatus.isFetching === true
);

const getCurrentRoundSubmissionIDs = createSelector(
    [ getCurrentRound ],
    (round) => {
        return round ? round.submissions.ids : [];
    }
);

const getCurrentRoundSubmissions = createSelector(
    [ getCurrentRoundSubmissionIDs, getSubmissions],
    (submissionIDs, submissions) => {
        return submissionIDs.map(submissionID => submissions[submissionID]);
    }
);


const getCurrentSubmission = createSelector(
    [ getCurrentSubmissionID, getSubmissions ],
    (id, submissions) => {
        return submissions[id];
    }
);

const getSubmissionOfID = (submissionID) => createSelector(
    [getSubmissions], submissions => submissions[submissionID]
);

const getSubmissionLoadingState = state => state.submissions.itemLoading === true;

const getSubmissionErrorState = state => state.submissions.itemLoadingError === true;

const getSubmissionsByRoundError = state => state.rounds.error;

const getSubmissionsByRoundLoadingState = state => state.submissions.itemsLoading === true;

export {
    getByGivenStatusesError,
    getByGivenStatusesLoading,
    getCurrentRoundID,
    getCurrentRound,
    getCurrentRoundSubmissionIDs,
    getCurrentRoundSubmissions,
    getCurrentSubmission,
    getCurrentSubmissionID,
    getRounds,
    getSubmissionsByRoundError,
    getSubmissionsByRoundLoadingState,
    getSubmissionLoadingState,
    getSubmissionErrorState,
    getSubmissionOfID,
    getSubmissionsByGivenStatuses,
};
