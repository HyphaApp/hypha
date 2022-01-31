import * as Selectors from '../submissions';

describe('Test the selector of submissions', () => {
    it('select submissions', () => {
        const state = {
            submissions: {
                byID: {
                    1: {title: 'submission1'},
                    2: {title: 'submission2'}
                }
            },
            loading: true
        };
        expect(Selectors.getSubmissions(state)).toEqual({
            1: {title: 'submission1'},
            2: {title: 'submission2'}
        });
    });
    it('get current submission id', () => {
        const state = {
            submissions: {
                current: 1
            },
            loading: true
        };
        expect(Selectors.getCurrentSubmissionID(state)).toEqual(1);
    });
    it('get review button status', () => {
        const state = {
            submissions: {
                showReviewForm: true
            },
            loading: true
        };
        expect(Selectors.getReviewButtonStatus(state)).toBe(true);
    });
    it('get current review', () => {
        const state = {
            submissions: {
                currentReview: 1
            },
            loading: true
        };
        expect(Selectors.getCurrentReview(state)).toEqual(1);
    });
    it('get review draft status', () => {
        const state = {
            submissions: {
                currentReview: 1,
                isReviewDraftExist: true
            },
            loading: true
        };
        expect(Selectors.getReviewDraftStatus(state)).toBe(true);
    });
    it('get determination button status', () => {
        const state = {
            submissions: {
                currentReview: 1,
                showDeterminationForm: true
            },
            loading: true
        };
        expect(Selectors.getDeterminationButtonStatus(state)).toBe(true);
    });
    it('get current determination', () => {
        const state = {
            submissions: {
                currentDetermination: 1,
                showDeterminationForm: true
            },
            loading: true
        };
        expect(Selectors.getCurrentDetermination(state)).toEqual(1);
    });
    it('get determination draft status', () => {
        const state = {
            submissions: {
                currentDetermination: 1,
                isDeterminationDraftExist: true
            },
            loading: true
        };
        expect(Selectors.getDeterminationDraftStatus(state)).toBe(true);
    });
    it('get submissions for listing', () => {
        const state = {
            submissions: {
                byID: {
                    1: {title: 'submission1'},
                    2: {title: 'submission2'}
                }
            },
            loading: true
        };
        expect(Selectors.getSubmissionsForListing(state)).toEqual([
            {title: 'submission1'},
            {title: 'submission2'}
        ]);
    });
    it('get current round submissions', () => {
        const state = {
            submissions: {
                byID: {
                    2: {title: 'submission2'},
                    3: {title: 'submission3'}
                }
            },
            loading: true,
            rounds: {
                byID: {
                    1: {id: 1, title: 'round1', submissions: {ids: [2, 3]}}
                },
                current: 1
            }
        };
        expect(Selectors.getCurrentRoundSubmissions(state)).toEqual([{title: 'submission2'}, {title: 'submission3'}]);
    });
    it('get current submission', () => {
        const state = {
            submissions: {
                byID: {
                    2: {id: 2, title: 'submission2'},
                    3: {id: 3, title: 'submission3'}
                },
                current: 2
            },
            loading: true
        };
        expect(Selectors.getCurrentSubmission(state)).toEqual({id: 2, title: 'submission2'});
    });
    it('get current statuses submissions', () => {
        const state = {
            submissions: {
                byID: {
                    2: {title: 'submission2'},
                    3: {title: 'submission3'}
                }
            },
            loading: true,
            statuses: {
                byStatuses: {
                    status1: [2],
                    status2: [3],
                    status3: [7, 8, 9]
                },
                current: ['status1', 'status2']
            }
        };
        expect(Selectors.getCurrentStatusesSubmissions(state)).toEqual([{title: 'submission2'}, {title: 'submission3'}]);
    });

    it('get current statuses submissions with byID null', () => {
        const state = {
            submissions: {
                byID: {}
            },
            loading: true,
            statuses: {
                byStatuses: {
                    status1: [2],
                    status2: [3],
                    status3: [7, 8, 9]
                },
                current: ['status1', 'status2']
            }
        };
        expect(Selectors.getCurrentStatusesSubmissions(state)).toEqual([]);
    });

    it('get submission loading state', () => {
        const state = {
            submissions: {
                current: 1,
                itemLoading: true
            },
            loading: true
        };
        expect(Selectors.getSubmissionLoadingState(state)).toBe(true);
    });
    it('get submission error', () => {
        const state = {
            submissions: {
                current: 1,
                itemLoadingError: false
            },
            loading: true
        };
        expect(Selectors.getSubmissionErrorState(state)).toBe(false);
    });
    it('get submission error', () => {
        const state = {
            rounds: {
                current: 1,
                error: true
            },
            loading: true
        };
        expect(Selectors.getSubmissionsByRoundError(state)).toBe(true);
    });
    it('get submission round loading', () => {
        const state = {
            submissions: {
                current: 1,
                itemsLoading: true
            },
            loading: true
        };
        expect(Selectors.getSubmissionsByRoundLoadingState(state)).toBe(true);
    });
    it('get submission of ID', () => {
        const submissionId = 1;
        const state = {
            submissions: {
                byID: {
                    1: {title: 'submission1'},
                    3: {title: 'submission3'}
                }
            },
            loading: true
        };
        expect(Selectors.getSubmissionOfID(submissionId)(state)).toEqual({title: 'submission1'});
    });
});
