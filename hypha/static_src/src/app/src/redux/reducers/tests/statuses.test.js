import * as Reducer from '../statuses';
import * as Actions from '../../actions/submissions';

describe('test reducer', () => {

    it('Test we get the initial data for undefined value of state', () => {
        expect(Reducer.current(undefined, {})).toBe[0];
        expect(Reducer.submissionsByStatuses(undefined, {})).toBe[0];
        expect(Reducer.statusFetchingState(undefined, {})).toEqual({isFetching: false, isError: false});
    });

    it('On set current statuses', () => {
        const action = {
            type: Actions.SET_CURRENT_STATUSES,
            statuses: ['status1', 'status2']
        };
        expect(Reducer.current(undefined, action)).toEqual(['status1', 'status2']);
    });

    it('On fail loading by statuses', () => {
        const action = {
            type: Actions.FAIL_LOADING_BY_STATUSES
        };
        expect(Reducer.statusFetchingState(undefined, action)).toEqual({
            isFetching: false,
            isErrored: true
        });
    });

    it('On start loading by statuses', () => {
        const action = {
            type: Actions.START_LOADING_BY_STATUSES
        };
        expect(Reducer.statusFetchingState(undefined, action)).toEqual({
            isFetching: true,
            isErrored: false
        });
    });

    it('On update by statuses', () => {
        const action = {
            type: Actions.UPDATE_BY_STATUSES
        };
        expect(Reducer.statusFetchingState(undefined, action)).toEqual({
            isFetching: false,
            isErrored: false
        });
    });

    it('On start loading by statuses', () => {
        const action = {
            type: Actions.START_LOADING_BY_STATUSES
        };
        expect(Reducer.statusFetchingState(undefined, action)).toEqual({
            isFetching: true,
            isErrored: false
        });
    });

    it('On clear all statuses', () => {
        const action = {
            type: Actions.CLEAR_ALL_STATUSES
        };
        expect(Reducer.submissionsByStatuses(undefined, action)).toEqual({});
    });

    it('On update by statuses using submissionsByStatuses', () => {
        const action = {
            type: Actions.UPDATE_BY_STATUSES,
            data: {
                results: [
                    {status: 'status1', id: 1},
                    {status: 'status2', id: 2}
                ]
            }
        };
        const state = {
            loading: false
        };
        expect(Reducer.submissionsByStatuses(state, action)).
            toEqual({loading: false, status1: [1], status2: [2]});
    });

    it('On update by statuses using submissionsByStatuses with state contains status already', () => {
        const action = {
            type: Actions.UPDATE_BY_STATUSES,
            data: {
                results: [
                    {status: 'status1', id: 1},
                    {status: 'status2', id: 2}
                ]
            }
        };
        const state = {
            loading: false,
            status1: [1, 3]
        };
        expect(Reducer.submissionsByStatuses(state, action)).
            toEqual({loading: false, status1: [1, 3], status2: [2]});
    });

    it('On update submission using submissionsByStatuses', () => {
        const action = {
            type: Actions.UPDATE_SUBMISSION,
            data: {
                id: 1,
                status: 'status1'
            }
        };
        const state = {
            status1: [1, 2, 3]
        };
        expect(Reducer.submissionsByStatuses(state, action)).
            toEqual({status1: [2, 3, 1]});
    });

    it('On update submission using submissionsByStatuses with state status empty', () => {
        const action = {
            type: Actions.UPDATE_SUBMISSION,
            data: {
                id: 1,
                status: 'status1'
            }
        };
        const state = {
            status2: []
        };
        expect(Reducer.submissionsByStatuses(state, action)).
            toEqual({status1: [1], status2: []});
    });
});
