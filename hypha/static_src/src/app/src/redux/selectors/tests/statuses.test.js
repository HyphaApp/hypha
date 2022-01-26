import * as Selectors from '../statuses';


describe('Test the selector of statuses', () => {
    it('select submissions by statuses', () => {
        const state = {
            statuses: {
                byStatuses: {
                    status1: [1, 2, 3],
                    status2: [4, 5, 6]
                },
                current: ['status1']
            },
            loading: true
        };
        expect(Selectors.getSubmissionsByStatuses(state)).toEqual({
            status1: [1, 2, 3],
            status2: [4, 5, 6]
        });
    });
    it('get current statuses', () => {
        const state = {
            statuses: {
                current: ['status1']
            },
            loading: true
        };
        expect(Selectors.getCurrentStatuses(state)).toEqual(['status1']);
    });
    it('get statuses fetching state', () => {
        const state = {
            statuses: {
                fetchingState: true
            }
        };
        expect(Selectors.getStatusesFetchingState(state)).toBe(true);
    });
    it('get submissionIDs for current statuses', () => {
        const state = {
            statuses: {
                byStatuses: {
                    status1: [1, 2, 3],
                    status2: [4, 5, 6],
                    status3: [7, 8, 9]
                },
                current: ['status1', 'status2']
            }
        };
        expect(Selectors.getSubmissionIDsForCurrentStatuses(state)).toEqual([1, 2, 3, 4, 5, 6]);
    });

    it('get submissionIDs for current statuses with empty byStatuses', () => {
        const state = {
            statuses: {
                byStatuses: {
                    status1: [],
                    status2: [],
                    status3: [7, 8, 9]
                },
                current: ['status1', 'status2']
            }
        };
        expect(Selectors.getSubmissionIDsForCurrentStatuses(state)).toEqual([]);
    });

    it('get submissionIDs for current statuses without current statuses', () => {
        const state = {
            statuses: {
                byStatuses: {
                    status1: [1, 2, 3],
                    status2: [4, 5, 6],
                    status3: [7, 8, 9]
                },
                current: []
            }
        };
        expect(Selectors.getSubmissionIDsForCurrentStatuses(state)).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9]);
    });

    it('get statuses error', () => {
        const state = {
            statuses: {
                fetchingState: {isFetching: false, isErrored: false}
            }
        };
        expect(Selectors.getByStatusesError(state)).toBe(false);
    });
    it('get statuses loading', () => {
        const state = {
            statuses: {
                fetchingState: {isFetching: false, isErrored: false}
            }
        };
        expect(Selectors.getByStatusesLoading(state)).toBe(false);
    });
});
