import * as Selectors from '../notes';


describe('Test the selector of notes', () => {

    it('Get notes', () => {
        expect(Selectors.getNotes({notes: {byID: {1: {id: 1}}}})).toEqual({1: {id: 1}});
    });

    it('Get notes of ID', () => {
        expect(Selectors.getNoteOfID(1)({notes: {byID: {1: {id: 1}, 2: {id: 2}}}})).toEqual({id: 1});
    });

    it('Get notes fetch state', () => {
        expect(Selectors.getNotesFetchState({notes: {isFetching: true}})).toBe(true);
    });

    it('Get notes error state', () => {
        expect(Selectors.getNotesErrorState({notes: {error: {errored: false}}})).toBe(false);
    });

    it('Get notes error message', () => {
        expect(Selectors.getNotesErrorMessage({notes: {error: {errored: false, message: 'error occured'}}})).toEqual('error occured');
    });

    it('Get note ids for submission of ID', () => {
        const state = {
            notes: {
                error: {errored: false, message: 'error occured'}
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: ['comments']}
                }
            }
        };
        expect(Selectors.getNoteIDsForSubmissionOfID(1)(state)).toEqual(['comments']);
    });

    it('Get note ids for submission of ID with comments null', () => {
        const state = {
            notes: {
                error: {errored: false, message: 'error occured'}
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: null}
                }
            }
        };
        expect(Selectors.getNoteIDsForSubmissionOfID(1)(state)).toEqual([]);
    });

    it('Get note ids for submission of ID with submissions null', () => {
        const state = {
            notes: {
                error: {errored: false, message: 'error occured'}
            },
            submissions: {
                byID: {
                    1: null
                }
            }
        };
        expect(Selectors.getNoteIDsForSubmissionOfID(1)(state)).toEqual([]);
    });

    it('Get latest note for submission of ID', () => {
        const state = {
            notes: {
                error: {errored: false, message: 'error occured'}
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: ['comments1', 'comments2']}
                }
            }
        };
        expect(Selectors.getLatestNoteForSubmissionOfID(1)(state)).toEqual('comments1');
    });

    it('Get notes for submission of ID', () => {
        const state = {
            notes: {
                error: {errored: false, message: 'error occured'},
                byID: {
                    2: {id: 2},
                    3: {id: 3}
                }
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getNotesForSubmission(1)(state)).toEqual([{id: 2}, {id: 3}]);
    });

    it('Get notes creating error ', () => {
        const state = {
            notes: {
                createError: {errored: false, message: 'error occured'},
                byID: {
                    2: {id: 2},
                    3: {id: 3}
                }
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getNoteCreatingErrors(state)).toEqual({errored: false, message: 'error occured'});
    });

    it('Get notes for creating error for submission of ID', () => {
        const state = {
            notes: {
                createError: {1: {errored: false, message: 'error occured'}},
                byID: {
                    2: {id: 2},
                    3: {id: 3}
                }
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getNoteCreatingErrorForSubmission(1)(state)).toEqual({errored: false, message: 'error occured'});
    });

    it('Get note creating state', () => {
        const state = {
            notes: {
                createError: {1: {errored: false, message: 'error occured'}},
                isCreating: false
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getNoteCreatingState(state)).toBe(false);
    });

    it('Get note creating state for submission', () => {
        const state = {
            notes: {
                createError: {1: {errored: false, message: 'error occured'}},
                isCreating: [2, 3, 4]
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getNoteCreatingStateForSubmission(1)(state)).toBe(false);
    });

    it('Get note editing state', () => {
        const state = {
            notes: {
                editing: {1: {errored: false, message: 'error occured'}},
                isCreating: [2, 3, 4]
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getNoteEditingState(state)).toEqual({1: {errored: false, message: 'error occured'}});
    });

    it('Get draft note for submission', () => {
        const state = {
            notes: {
                editing: {1: {errored: false, message: 'error occured'}},
                isCreating: [2, 3, 4]
            },
            submissions: {
                byID: {
                    1: {id: 1, comments: [2, 3]}
                }
            }
        };
        expect(Selectors.getDraftNoteForSubmission(1)(state)).toEqual({errored: false, message: 'error occured'});
    });
});
