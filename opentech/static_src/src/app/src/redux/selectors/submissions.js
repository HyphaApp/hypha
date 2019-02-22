import { createSelector } from 'reselect';

import {
    getCurrentRoundSubmissionIDs,
} from '@selectors/rounds';

import {
    getSubmissionIDsForCurrentStatuses,
} from '@selectors/statuses';

const getSubmissions = state => state.submissions.byID;

const getCurrentSubmissionID = state => state.submissions.current;


const getCurrentRoundSubmissions = createSelector(
    [ getCurrentRoundSubmissionIDs, getSubmissions],
    (submissionIDs, submissions) => {
        return submissionIDs.map(submissionID => submissions[submissionID]);
    }
);


const getCurrentStatusesSubmissions = createSelector(
    [ getSubmissionIDsForCurrentStatuses, getSubmissions],
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
    getCurrentRoundSubmissions,
    getCurrentSubmission,
    getCurrentSubmissionID,
    getSubmissionsByRoundError,
    getSubmissionsByRoundLoadingState,
    getSubmissionLoadingState,
    getSubmissionErrorState,
    getSubmissionOfID,
    getCurrentStatusesSubmissions,
};
