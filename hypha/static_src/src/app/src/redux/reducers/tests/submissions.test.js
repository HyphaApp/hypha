import {
    isDeterminationDraftExist,
    currentDetermination,
    toggleDeterminationForm,
    isReviewDraftExist,
    currentReview,
    toggleReviewForm,
    currentSubmission,
    submissionsByID,
    submission
} from '../submissions';
import * as SubmissionsActions from '../../actions/submissions';
import * as NotesActions from '../../actions/notes';


describe('test reducer', () => {

    it('Test we get the initial data for undefined value of state', () => {
        expect(isDeterminationDraftExist(undefined, {})).toBe(false);
        expect(currentDetermination(undefined, {})).toBeFalsy();
        expect(toggleDeterminationForm(undefined, {})).toBe(false);
        expect(isReviewDraftExist(undefined, {})).toBe(false);
        expect(currentReview(undefined, {})).toBeFalsy();
        expect(toggleReviewForm(undefined, {})).toBe(false);
        expect(currentSubmission(undefined, {})).toBeFalsy();
        expect(submissionsByID(undefined, {})).toMatchObject({});
        expect(submission(undefined, {})).toEqual({comments: []});
    });

    it('On clear determination draft', () => {
        const action = SubmissionsActions.clearDeterminationDraftAction();
        expect(isDeterminationDraftExist(undefined, action)).toBe(false);
    });

    it('On set current determination', () => {
        const determinationId = 1;
        const action = SubmissionsActions.setCurrentDeterminationAction(determinationId);
        expect(currentDetermination(undefined, action)).toEqual(determinationId);
    });

    it('On clear current determination', () => {
        const action = SubmissionsActions.clearCurrentDeterminationAction();
        expect(currentDetermination(undefined, action)).toBeFalsy();
    });

    it('On toggle determination form', () => {
        const status = true;
        const action = SubmissionsActions.toggleDeterminationFormAction(status);
        expect(toggleDeterminationForm(undefined, action)).toBe(true);
    });

    it('On set current review', () => {
        const reviewId = 1;
        const action = SubmissionsActions.setCurrentReviewAction(reviewId);
        expect(currentReview(undefined, action)).toEqual(reviewId);
    });

    it('On clear current review', () => {
        const action = SubmissionsActions.clearCurrentReviewAction();
        expect(currentReview(undefined, action)).toBeFalsy();
    });

    it('On toggle review form', () => {
        const status = true;
        const action = SubmissionsActions.toggleReviewFormAction(status);
        expect(toggleReviewForm(undefined, action)).toBe(true);
    });

    it('On set current submission', () => {
        const action = {
            type: SubmissionsActions.SET_CURRENT_SUBMISSION,
            id: 1
        };
        expect(currentSubmission(undefined, action)).toEqual(1);
    });

    it('On clear current submission', () => {
        const action = SubmissionsActions.clearCurrentSubmission();
        expect(currentSubmission(undefined, action)).toBeFalsy();
    });

    it('On clear all submissions', () => {
        const action = SubmissionsActions.clearAllSubmissionsAction();
        expect(currentSubmission(undefined, action)).toBeFalsy();
    });

    it('On clear all submissions in submissionsByID', () => {
        const action = SubmissionsActions.clearAllSubmissionsAction();
        expect(submissionsByID(undefined, action)).toMatchObject({});
    });

    it('On clear all submissions in submissionsByID', () => {
        const action = SubmissionsActions.clearAllSubmissionsAction();
        expect(submissionsByID(undefined, action)).toMatchObject({});
    });

    it('On fetch determination draft', () => {
        const action = {
            type: SubmissionsActions.FETCH_DETERMINATION_DRAFT,
            data: {
                isDraft: true
            }
        };
        expect(isDeterminationDraftExist(undefined, action)).toBe(true);
    });

    it('On fetch determination draft on false', () => {
        const action = {
            type: SubmissionsActions.FETCH_DETERMINATION_DRAFT,
            data: {
                isDraft: false
            }
        };
        expect(isDeterminationDraftExist(undefined, action)).toBe(false);
    });

    it('On fetch review draft', () => {
        const action = {
            type: SubmissionsActions.FETCH_REVIEW_DRAFT,
            data: {
                isDraft: true
            }
        };
        expect(isReviewDraftExist(undefined, action)).toBe(true);
    });

    it('On fetch review draft on false', () => {
        const action = {
            type: SubmissionsActions.FETCH_REVIEW_DRAFT,
            data: {
                isDraft: false
            }
        };
        expect(isReviewDraftExist(undefined, action)).toBe(false);
    });

    it('On clear review draft', () => {
        const action = {
            type: SubmissionsActions.CLEAR_REVIEW_DRAFT
        };
        expect(isReviewDraftExist(undefined, action)).toBe(false);
    });

    it('On start loading submission', () => {
        const action = {
            type: SubmissionsActions.START_LOADING_SUBMISSION,
            submissionID: 1
        };
        const state = {
            1: {id: 1},
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual({
            1: {id: 1, isFetching: true, isErrored: false},
            loading: false
        });
    });

    it('On fail loading submission', () => {
        const action = {
            type: SubmissionsActions.FAIL_LOADING_SUBMISSION,
            submissionID: 1
        };
        const state = {
            1: {id: 1},
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual({
            1: {id: 1, isFetching: false, isErrored: true},
            loading: false
        });
    });

    it('On update submission', () => {
        const action = {
            type: SubmissionsActions.UPDATE_SUBMISSION,
            submissionID: 1,
            data: {count: 1},
            changedLocally: true
        };
        const state = {
            1: {id: 1},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                isFetching: false,
                isErrored: true,
                count: 1,
                isFetching: false,
                isErrored: false,
                isExecutingAction: false,
                isExecutingActionErrored: false,
                executionActionError: undefined,
                changedLocally: true
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On create note without comments', () => {
        const action = {
            type: NotesActions.CREATE_NOTE,
            data: {id: 1},
            submissionID: 1
        };
        const state = {
            1: {id: 1},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [1]
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On create note with comments', () => {
        const action = {
            type: NotesActions.CREATE_NOTE,
            data: {id: 1},
            submissionID: 1
        };
        const state = {
            1: {id: 1, comments: ['abc']},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [1, 'abc']
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On update note', () => {
        const action = {
            type: NotesActions.UPDATE_NOTE,
            data: {id: 1},
            submissionID: 1,
            note: {id: 2}
        };
        const state = {
            1: {id: 1, comments: [2, 3]},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [1, 3]
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On update note with state comments empty', () => {
        const action = {
            type: NotesActions.UPDATE_NOTE,
            data: {id: 1},
            submissionID: 1,
            note: {id: 2}
        };
        const state = {
            1: {id: 1, comments: []},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [1]
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On fail executing submission', () => {
        const action = {
            type: SubmissionsActions.FAIL_EXECUTING_SUBMISSION_ACTION,
            submissionID: 1,
            error: 'error occured'
        };
        const state = {
            1: {id: 1, comments: [2, 3]},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [2, 3],
                isExecutingAction: false,
                isExecutingActionErrored: true,
                executionActionError: 'error occured'
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On start executing submission', () => {
        const action = {
            type: SubmissionsActions.START_EXECUTING_SUBMISSION_ACTION,
            submissionID: 1
        };
        const state = {
            1: {id: 1, comments: [2, 3]},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [2, 3],
                isExecutingAction: true,
                isExecutingActionErrored: false,
                executionActionError: undefined
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On update notes', () => {
        const action = {
            type: NotesActions.UPDATE_NOTES,
            submissionID: 1,
            data: {
                results: [{id: 4}, {id: 5}]
            }
        };
        const state = {
            1: {id: 1, comments: [2, 3]},
            loading: false
        };
        const expected = {
            1: {
                id: 1,
                comments: [4, 5, 2, 3]
            },
            loading: false
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On update submissions by statuses', () => {
        const action = {
            type: SubmissionsActions.UPDATE_BY_STATUSES,
            submissionID: 1,
            data: {
                results: [{id: 4, title2: 'a'}]
            }
        };
        const state = {
            1: {id: 1},
            4: {title1: 'in state'},
            loading: false
        };
        const expected = {
            1: {
                id: 1
            },
            loading: false,
            4: {
                title1: 'in state',
                id: 4,
                title2: 'a',
                isFetching: false,
                isErrored: true,
                isFetching: false,
                isErrored: false,
                isExecutingAction: false,
                isExecutingActionErrored: false,
                executionActionError: undefined,
                changedLocally: false
            }
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });

    it('On update submissions by rounds', () => {
        const action = {
            type: SubmissionsActions.UPDATE_SUBMISSIONS_BY_ROUND,
            submissionID: 1,
            data: {
                results: [{id: 4, title2: 'a'}]
            }
        };
        const state = {
            1: {id: 1},
            4: {title1: 'in state'},
            loading: false
        };
        const expected = {
            1: {
                id: 1
            },
            loading: false,
            4: {
                title1: 'in state',
                id: 4,
                title2: 'a',
                isFetching: false,
                isErrored: true,
                isFetching: false,
                isErrored: false,
                isExecutingAction: false,
                isExecutingActionErrored: false,
                executionActionError: undefined,
                changedLocally: false
            }
        };
        expect(submissionsByID(state, action)).toEqual(expected);
    });
});
