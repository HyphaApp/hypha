import * as Selectors from '../rounds';


describe('Test the selector of rounds', () => {
    it('select rounds', () => {
        const state = {
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
                },
                current: 1
            },
            loading: true
        };
        expect(Selectors.getRounds(state)).toEqual({
            1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
        });
    });
    it('select current round id', () => {
        const state = {
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
                },
                current: 1
            },
            loading: true
        };
        expect(Selectors.getCurrentRoundID(state)).toEqual(1);
    });
    it('select current round', () => {
        const state = {
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
                },
                current: 1
            },
            loading: true
        };
        expect(Selectors.getCurrentRound(state)).toEqual({id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}});
    });
    it('select current round submission ids with rounds byId null', () => {
        const state = {
            rounds: {
                byID: {
                    1: null
                },
                current: 1
            },
            loading: true
        };
        expect(Selectors.getCurrentRoundSubmissionIDs(state)).toEqual([]);
    });

    it('select current round submission ids', () => {
        const state = {
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
                },
                current: 1
            },
            loading: true
        };
        expect(Selectors.getCurrentRoundSubmissionIDs(state)).toEqual([2, 3, 4]);
    });

    it('select rounds fetching', () => {
        const state = {
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
                },
                current: 1,
                isFetching: true,
                isErrored: false
            },
            loading: true
        };
        expect(Selectors.getRoundsFetching(state)).toBe(true);
    });
    it('select rounds errored', () => {
        const state = {
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3, 4]}}
                },
                current: 1,
                isFetching: true,
                isErrored: false
            },
            loading: true
        };
        expect(Selectors.getRoundsErrored(state)).toBe(false);
    });
});
