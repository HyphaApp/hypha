import { createSelector } from 'reselect';

const getRounds = state => state.rounds.byID;

const getCurrentRoundID = state => state.rounds.current;

const getCurrentRound = createSelector(
    [ getCurrentRoundID, getRounds],
    (id, rounds) => {
        return rounds[id];
    }
);

const getCurrentRoundSubmissionIDs = createSelector(
    [ getCurrentRound ],
    (round) => {
        return round ? round.submissions.ids : [];
    }
);

const getRoundsFetching = state => state.rounds.isFetching === true;

const getRoundsErrored = state => state.rounds.isErrored === true;

export {
    getRounds,
    getCurrentRound,
    getCurrentRoundID,
    getCurrentRoundSubmissionIDs,
    getRoundsErrored,
    getRoundsFetching,
};

