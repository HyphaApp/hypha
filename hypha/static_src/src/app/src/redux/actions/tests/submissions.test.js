import * as actions from '../submissions';
import {CALL_API} from '@middleware/api';
import api from '@api';


describe('Test actions', () => {

    it('Should return the clear Determination Draft Action type', () => {
        const expectedResult = {
            type: actions.CLEAR_DETERMINATION_DRAFT
        };
        const action = actions.clearDeterminationDraftAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear all submissions Action type', () => {
        const expectedResult = {
            type: actions.CLEAR_ALL_SUBMISSIONS
        };
        const action = actions.clearAllSubmissionsAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear all statuses Action type', () => {
        const expectedResult = {
            type: actions.CLEAR_ALL_STATUSES
        };
        const action = actions.clearAllStatusesAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear all rounds Action type', () => {
        const expectedResult = {
            type: actions.CLEAR_ALL_ROUNDS
        };
        const action = actions.clearAllRoundsAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear all current determination', () => {
        const expectedResult = {
            type: actions.CLEAR_CURRENT_DETERMINATION
        };
        const action = actions.clearCurrentDeterminationAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear review draft', () => {
        const expectedResult = {
            type: actions.CLEAR_REVIEW_DRAFT
        };
        const action = actions.clearReviewDraftAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear current review', () => {
        const expectedResult = {
            type: actions.CLEAR_CURRENT_REVIEW
        };
        const action = actions.clearCurrentReviewAction();
        expect(action).toEqual(expectedResult);
    });

    it('Should return the clear current submission', () => {
        const expectedResult = {
            type: actions.CLEAR_CURRENT_SUBMISSION
        };
        const action = actions.clearCurrentSubmission();
        expect(action).toEqual(expectedResult);
    });

    it('Should return toggle determination action type', () => {
        const status = true;
        const expectedResult = {
            type: actions.TOGGLE_DETERMINATION_FORM,
            status
        };
        const action = actions.toggleDeterminationFormAction(status);
        expect(action).toEqual(expectedResult);
    });

    it('Should return set current determination action type', () => {
        const determinationId = 1;
        const expectedResult = {
            type: actions.SET_CURRENT_DETERMINATION,
            determinationId
        };
        const action = actions.setCurrentDeterminationAction(determinationId);
        expect(action).toEqual(expectedResult);
    });

    it('Should return toggle review form action type', () => {
        const status = true;
        const expectedResult = {
            type: actions.TOGGLE_REVIEW_FORM,
            status
        };
        const action = actions.toggleReviewFormAction(status);
        expect(action).toEqual(expectedResult);
    });

    it('Should return set current review action type', () => {
        const reviewId = 1;
        const expectedResult = {
            type: actions.SET_CURRENT_REVIEW,
            reviewId
        };
        const action = actions.setCurrentReviewAction(reviewId);
        expect(action).toEqual(expectedResult);
    });

    it('Should return append NoteID For Submission action type', () => {
        const submissionID = 1;
        const noteID = 2;
        const expectedResult = {
            type: actions.ADD_NOTE_FOR_SUBMISSION,
            submissionID,
            noteID
        };
        const action = actions.appendNoteIDForSubmission(submissionID, noteID);
        expect(action).toEqual(expectedResult);
    });

    it('Should return set current Submission round action type', () => {
        const submissionID = 1;
        const results = [];
        actions.setCurrentSubmissionRound(submissionID)(result => results.push(result));
        expect(results[0].type).toEqual(actions.SET_CURRENT_SUBMISSION_ROUND);
        expect(results.length).toEqual(5);
    });

    it('Should return set current Submission action type', () => {
        const submissionID = 1;
        const results = [];
        actions.setCurrentSubmission(submissionID)(result => results.push(result));
        expect(results.length).toEqual(8);
        expect(results[7].type).toEqual(actions.SET_CURRENT_SUBMISSION);
    });

    it('Should return set current statuses action type', () => {
        const statuses = ['status1', 'status2'];
        const results = [];
        actions.setCurrentStatuses(statuses)(result => results.push(result));
        expect(results[0].type).toEqual(actions.SET_CURRENT_STATUSES);
        expect(results.length).toEqual(5);
    });

    it('Should return an error if statuses is not of type array for set current statuses action type', () => {
        const statuses = null;
        const results = [];
        try {
            actions.setCurrentStatuses(statuses)(result => results.push(result));
        }
        catch (e) {
            expect(e).toEqual(new Error('Statuses have to be an array of statuses'));
        }
        expect(results.length).toEqual(0);
    });

    it('Should return load submission from url action type', () => {
        const params = '?submission=2';
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                submissions: {
                    current: 1
                }
            };
        };
        expect(actions.loadSubmissionFromURL(params)(firstFunc, secFunc)).toBe(true);
        expect(results.length).toEqual(1);
    });

    it('Should return load submission from url action type with both url id & submission id is equal', () => {
        const params = '?submission=2';
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                submissions: {
                    current: 2
                }
            };
        };
        expect(actions.loadSubmissionFromURL(params)(firstFunc, secFunc)).toBe(true);
        expect(results.length).toEqual(0);
    });

    it("Should return load submission from url if url doesn't have id action type", () => {
        const params = '';
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                submissions: {
                    current: 1
                }
            };
        };
        expect(actions.loadSubmissionFromURL(params)(firstFunc, secFunc)).toBe(false);
        expect(results.length).toEqual(0);
    });

    it('Should return clear current submission param action type', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: 'abc'
                    }
                }
            };
        };
        actions.clearCurrentSubmissionParam()(firstFunc, secFunc);
        expect(results.length).toEqual(1);
    });

    it('Should return clear current submission param action type if search is empty', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: ''
                    }
                }
            };
        };
        actions.clearCurrentSubmissionParam()(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return set current submission param action type', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                submissions: {
                    current: 1
                }
            };
        };
        actions.setCurrentSubmissionParam()(firstFunc, secFunc);
        expect(results.length).toEqual(1);
    });

    it('Should return fetchDeterminationDraft action type', () => {
        const submissionID = 1;
        const action = actions.fetchDeterminationDraft(submissionID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_SUBMISSION, actions.FETCH_DETERMINATION_DRAFT, actions.FAIL_LOADING_SUBMISSION],
                endpoint: api.fetchDeterminationDraft(submissionID)
            },
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetchReviewDraft action type', () => {
        const submissionID = 1;
        const action = actions.fetchReviewDraft(submissionID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_SUBMISSION, actions.FETCH_REVIEW_DRAFT, actions.CLEAR_REVIEW_DRAFT],
                endpoint: api.fetchReviewDraft(submissionID)
            },
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetchRound action type', () => {
        const roundID = 1;
        const action = actions.fetchRound(roundID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_ROUND, actions.UPDATE_ROUND, actions.FAIL_LOADING_ROUND],
                endpoint: api.fetchRound(roundID)
            },
            roundID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetchRounds action type', () => {
        const action = actions.fetchRounds();
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_ROUNDS, actions.UPDATE_ROUNDS, actions.FAIL_LOADING_ROUNDS],
                endpoint: api.fetchRounds()
            }
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetchSubmissionsByRound action type', () => {
        const roundID = 1;
        const filters = null;
        const action = actions.fetchSubmissionsByRound(roundID, filters);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_SUBMISSIONS_BY_ROUND, actions.UPDATE_SUBMISSIONS_BY_ROUND, actions.FAIL_LOADING_SUBMISSIONS_BY_ROUND],
                endpoint: api.fetchSubmissionsByRound(roundID, filters)
            },
            roundID,
            filters
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetchSubmissionsByStatuses action type', () => {
        const statuses = ['status1'];
        const filters = null;
        const action = actions.fetchSubmissionsByStatuses(statuses, filters);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_BY_STATUSES, actions.UPDATE_BY_STATUSES, actions.FAIL_LOADING_BY_STATUSES],
                endpoint: api.fetchSubmissionsByStatuses(statuses, filters)
            },
            statuses,
            filters
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetchSubmission action type', () => {
        const submissionID = 1;
        const action = actions.fetchSubmission(submissionID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_LOADING_SUBMISSION, actions.UPDATE_SUBMISSION, actions.FAIL_LOADING_SUBMISSION],
                endpoint: api.fetchSubmission(submissionID)
            },
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return executeSubmissionAction action type', () => {
        const submissionID = 1;
        const act = null;
        const action = actions.executeSubmissionAction(submissionID, act);
        const expectedResult = {
            [CALL_API]: {
                types: [
                    actions.START_EXECUTING_SUBMISSION_ACTION,
                    actions.UPDATE_SUBMISSION,
                    actions.FAIL_EXECUTING_SUBMISSION_ACTION
                ],
                endpoint: api.executeSubmissionAction(submissionID, act)
            },
            submissionID,
            changedLocally: true
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return setSubmissionParam action type with shouldset true', () => {
        const results = [];
        const id = 1;
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission='
                    }
                },
                submissions: {
                    current: 1
                }
            };
        };
        actions.setSubmissionParam(id)(firstFunc, secFunc);
        expect(results.length).toEqual(1);
    });

    it('Should return setSubmissionParam action type with shouldUpdate true', () => {
        const results = [];
        const id = 1;
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission='
                    }
                },
                submissions: {
                    current: 2
                }
            };
        };
        actions.setSubmissionParam(id)(firstFunc, secFunc);
        expect(results.length).toEqual(1);
    });

    it('Should return setSubmissionParam action type with id null', () => {
        const results = [];
        const id = null;
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission='
                    }
                },
                submissions: {
                    current: 2
                }
            };
        };
        actions.setSubmissionParam(id)(firstFunc, secFunc);
        expect(results.length).toEqual(1);
        expect(typeof results[0]).toEqual('function');
    });

    it('Should return setSubmissionParam action type with shouldSet & shouldUpdate false & id not null', () => {
        const results = [];
        const id = 2;
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission=2'
                    }
                },
                submissions: {
                    current: 2
                }
            };
        };
        actions.setSubmissionParam(id)(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return loadCurrentRound action type without required fields ', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission='
                    }
                },
                rounds: {
                    current: 2,
                    byID: {
                        2: {
                            id: 2,
                            isFetching: false,
                            submissions: {ids: Array(22), isFetching: false}
                        }
                    }

                }
            };
        };
        actions.loadCurrentRound(['workflow'])(firstFunc, secFunc);
        expect(results.length).toEqual(1);
        expect(typeof results[0]).toEqual('object');
        expect(results[0].roundID).toEqual(2);
    });

    it('Should return loadCurrentRound action type without having byID', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission='
                    }
                },
                rounds: {
                    current: 2,
                    byID: { }
                }
            };
        };
        actions.loadCurrentRound(['workflow'])(firstFunc, secFunc);
        expect(results.length).toEqual(1);
        expect(typeof results[0]).toEqual('object');
        expect(results[0].roundID).toEqual(2);
    });

    it('Should return loadCurrentRound action type with required fields ', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: '?submission='
                    }
                },
                rounds: {
                    current: 2,
                    byID: {
                        2: {
                            id: 2,
                            isFetching: false,
                            submissions: {ids: Array(22), isFetching: false},
                            workflow: true
                        }
                    }

                }
            };
        };
        actions.loadCurrentRound(['workflow'])(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return loadRounds action type with rounds exist', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: ''
                    }
                },
                rounds: {
                    current: 2,
                    byID: {
                        2: {
                            id: 2,
                            isFetching: false,
                            submissions: {ids: Array(22), isFetching: false},
                            workflow: true
                        }
                    }

                }
            };
        };
        actions.loadRounds()(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return loadRounds action type without rounds', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: ''
                    }
                },
                rounds: {
                    current: 2,
                    byID: {}
                }
            };
        };
        actions.loadRounds()(firstFunc, secFunc);
        expect(results.length).toEqual(1);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_LOADING_ROUNDS, actions.UPDATE_ROUNDS, actions.FAIL_LOADING_ROUNDS]);
    });

    it('Should return loadCurrentRoundSubmissions action type without filters', () => {
        const results = [];
        const firstFunc = result => Promise.resolve(results.push(result));
        const secFunc = () => {
            return {
                router: {
                    location: {
                        search: ''
                    }
                },
                rounds: {
                    current: 2,
                    byID: {
                        2: {
                            id: 2,
                            isFetching: false,
                            submissions: {ids: [1, 3, 4], isFetching: false},
                            workflow: true
                        }
                    }
                }
            };
        };
        actions.loadCurrentRoundSubmissions()(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return loadCurrentRoundSubmissions action type with filters', () => {
        const results = [];
        const firstFunc = result => Promise.resolve(results.push(result));
        const secFunc = () => {
            return {
                rounds: {
                    current: 2,
                    byID: {
                        2: {
                            id: 2,
                            isFetching: false,
                            submissions: {ids: [1, 3, 4], isFetching: false},
                            workflow: true
                        }
                    }
                },
                statuses: {
                    current: ['status1']
                },
                SubmissionFiltersContainer: {
                    filterQuery: [{key: 'key1', value: [1]}]
                }
            };
        };
        actions.loadCurrentRoundSubmissions()(firstFunc, secFunc);
        expect(results.length).toEqual(1);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_LOADING_SUBMISSIONS_BY_ROUND, actions.UPDATE_SUBMISSIONS_BY_ROUND, actions.FAIL_LOADING_SUBMISSIONS_BY_ROUND]);
    });

    it('Should return loadSubmissionsForCurrentStatus action type with filters', () => {
        const results = [];
        const firstFunc = result => Promise.resolve(results.push(result));
        const secFunc = () => {
            return {
                statuses: {
                    current: ['status1'],
                    byStatuses: {
                        status1: [1, 3]
                    }
                },
                SubmissionFiltersContainer: {
                    filterQuery: [{key: 'key1', value: [1]}]
                },
                submissions: {
                    byID: {
                        1: {id: 1},
                        3: {id: 3}
                    }
                }
            };
        };
        actions.loadSubmissionsForCurrentStatus()(firstFunc, secFunc);
        expect(results.length).toEqual(1);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_LOADING_BY_STATUSES, actions.UPDATE_BY_STATUSES, actions.FAIL_LOADING_BY_STATUSES]);
    });

    it('Should return loadSubmissionsForCurrentStatus action type without filters', () => {
        const results = [];
        const firstFunc = result => Promise.resolve(results.push(result));
        const secFunc = () => {
            return {
                statuses: {
                    current: ['status1'],
                    byStatuses: {
                        status1: [1, 3]
                    }
                },
                submissions: {
                    byID: {
                        1: {id: 1},
                        3: {id: 3}
                    }
                }
            };
        };
        actions.loadSubmissionsForCurrentStatus()(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return loadCurrentSubmission action type without current submission', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                statuses: {
                    current: ['status1'],
                    byStatuses: {
                        status1: [1, 3]
                    }
                },
                submissions: {
                    byID: {
                        1: {id: 1},
                        3: {id: 3}
                    },
                    current: null
                }
            };
        };
        actions.loadCurrentSubmission([], {bypassCache: true})(firstFunc, secFunc);
        expect(results.length).toEqual(0);
    });

    it('Should return loadCurrentSubmission action type with current submission & not bypasscache', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                statuses: {
                    current: ['status1'],
                    byStatuses: {
                        status1: [1, 3]
                    }
                },
                submissions: {
                    byID: {
                        1: {id: 1, questions: {title: 'one'}},
                        3: {id: 3}
                    },
                    current: 1
                }
            };
        };
        const action = actions.loadCurrentSubmission(['questions'], {bypassCache: false})(firstFunc, secFunc);
        expect(results.length).toEqual(0);
        expect(action).toBeNull();
    });

    it('Should return loadCurrentSubmission action type with current submission & with bypasscache', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        const secFunc = () => {
            return {
                statuses: {
                    current: ['status1'],
                    byStatuses: {
                        status1: [1, 3]
                    }
                },
                submissions: {
                    byID: {
                        1: {id: 1, questions: {title: 'one'}},
                        3: {id: 3}
                    },
                    current: 1
                }
            };
        };
        const action = actions.loadCurrentSubmission(['questions'], {bypassCache: true})(firstFunc, secFunc);
        expect(results.length).toEqual(3);
    });
});
