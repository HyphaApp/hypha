import * as Reducer from '../rounds';
import * as Actions from '../../actions/submissions';

describe('test reducer', () => {

    it('Test we get the initial data for undefined value of state', () => {
        expect(Reducer.currentRound(undefined, {})).toBeNull();
        expect(Reducer.roundsFetching(undefined, {})).toBe(false);
        expect(Reducer.roundsErrored(undefined, {})).toBe(false);
        expect(Reducer.errorMessage(undefined, {})).toBeFalsy();
        expect(Reducer.roundsByID(undefined, {})).toMatchObject({});
        expect(Reducer.round(undefined, {})).toEqual({id: null, submissions: {ids: [], isFetching: false}, isFetching: false});
        expect(Reducer.submissions(undefined, {})).toEqual({ids: [], isFetching: false});
    });

    it('On set current round', () => {
        const action = {
            type: Actions.SET_CURRENT_SUBMISSION_ROUND,
            id: 1
        };
        expect(Reducer.currentRound(undefined, action)).toEqual(1);
    });

    it('On fail loading rounds', () => {
        const action = {
            type: Actions.FAIL_LOADING_ROUNDS
        };
        expect(Reducer.roundsFetching(undefined, action)).toBe(false);
    });

    it('On start loading rounds', () => {
        const action = {
            type: Actions.START_LOADING_ROUNDS
        };
        expect(Reducer.roundsFetching(undefined, action)).toBe(true);
    });

    it('On update rounds', () => {
        const action = {
            type: Actions.UPDATE_ROUNDS
        };
        expect(Reducer.roundsFetching(undefined, action)).toBe(false);
    });

    it('On fail loading rounds using roundsErrored', () => {
        const action = {
            type: Actions.FAIL_LOADING_ROUNDS
        };
        expect(Reducer.roundsErrored(undefined, action)).toBe(true);
    });

    it('On start loading rounds using roundsErrored', () => {
        const action = {
            type: Actions.START_LOADING_ROUNDS
        };
        expect(Reducer.roundsErrored(undefined, action)).toBe(false);
    });

    it('On update rounds using roundsErrored', () => {
        const action = {
            type: Actions.UPDATE_ROUNDS
        };
        expect(Reducer.roundsErrored(undefined, action)).toBe(false);
    });

    it('On fail loading submissions by rounds', () => {
        const action = {
            type: Actions.FAIL_LOADING_SUBMISSIONS_BY_ROUND,
            message: 'text'
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('text');
    });

    it('On fail loading round', () => {
        const action = {
            type: Actions.FAIL_LOADING_ROUND,
            message: 'text'
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('text');
    });

    it('On fail loading round with empty message', () => {
        const action = {
            type: Actions.FAIL_LOADING_ROUND,
            message: null
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('');
    });

    it('On update submissions by round', () => {
        const action = {
            type: Actions.UPDATE_SUBMISSIONS_BY_ROUND
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('');
    });

    it('On start loading submissions by round', () => {
        const action = {
            type: Actions.START_LOADING_SUBMISSIONS_BY_ROUND
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('');
    });

    it('On update round', () => {
        const action = {
            type: Actions.UPDATE_ROUND
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('');
    });

    it('On start loading round', () => {
        const action = {
            type: Actions.START_LOADING_ROUND
        };
        expect(Reducer.errorMessage(undefined, action)).toEqual('');
    });

    it('On update submissions by round using roundsByID', () => {
        const action = {
            type: Actions.UPDATE_SUBMISSIONS_BY_ROUND,
            roundID: 1,
            data: {results: [{id: 2}, {id: 3}]}
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                title: 'one',
                id: 1,
                submissions: {ids: [2, 3], isFetching: false}
            },
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On fail loading submissions by round using roundsByID', () => {
        const action = {
            type: Actions.FAIL_LOADING_SUBMISSIONS_BY_ROUND,
            roundID: 1
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                submissions: {ids: [], isFetching: false},
                title: 'one'
            },
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On start loading submissions by round using roundsByID', () => {
        const action = {
            type: Actions.START_LOADING_SUBMISSIONS_BY_ROUND,
            roundID: 1,
            data: {results: [{id: 2}, {id: 3}]}
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                submissions: {ids: [], isFetching: true},
                title: 'one'
            },
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On update round using roundsByID', () => {
        const action = {
            type: Actions.UPDATE_ROUND,
            roundID: 1,
            data: {results: [{id: 2}, {id: 3}]}
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                title: 'one',
                results: [{id: 2}, {id: 3}],
                isFetching: false
            },
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On start loading round using roundsByID', () => {
        const action = {
            type: Actions.START_LOADING_ROUND,
            roundID: 1,
            data: {results: [{id: 2}, {id: 3}]}
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                title: 'one',
                id: 1,
                isFetching: true
            },
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On fail loading round using roundsByID', () => {
        const action = {
            type: Actions.FAIL_LOADING_ROUND,
            roundID: 1,
            data: {results: [{id: 2}, {id: 3}]}
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                title: 'one',
                isFetching: false
            },
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On update rounds using roundsByID', () => {
        const action = {
            type: Actions.UPDATE_ROUNDS,
            roundID: 1,
            data: {results: [{id: 2}, {id: 3}]}
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {
            1: {
                title: 'one'
            },
            2: {id: 2, submissions: {ids: [], isFetching: false}, isFetching: false},
            3: {id: 3, submissions: {ids: [], isFetching: false}, isFetching: false},
            loading: false
        };
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });

    it('On clear all rounds using roundsByID', () => {
        const action = {
            type: Actions.CLEAR_ALL_ROUNDS
        };
        const state = {
            1: {
                title: 'one'
            },
            loading: false
        };
        const expected = {};
        expect(Reducer.roundsByID(state, action)).toEqual(expected);
    });
});
