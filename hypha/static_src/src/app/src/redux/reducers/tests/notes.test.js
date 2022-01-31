import * as Reducer from '../notes';
import * as Actions from '../../actions/notes';

describe('test reducer', () => {

    it('Test we get the initial data for undefined value of state', () => {
        expect(Reducer.notesFetching(undefined, {})).toBe(false);
        expect(Reducer.notesErrored(undefined, {})).toEqual({errored: false, message: null},);
        expect(Reducer.note(undefined, {})).toBeFalsy();
        expect(Reducer.notesFailedCreating(undefined, {})).toMatchObject({});
        expect(Reducer.notesByID(undefined, {})).toMatchObject({});
        expect(Reducer.notesCreating(undefined, {})).toEqual([]);
        expect(Reducer.editingNote(undefined, {})).toMatchObject({});
    });

    it('On start fetching notes', () => {
        const action = {
            type: Actions.START_FETCHING_NOTES
        };
        expect(Reducer.notesFetching(undefined, action)).toEqual(true);
    });

    it('On update notes', () => {
        const action = {
            type: Actions.UPDATE_NOTES
        };
        expect(Reducer.notesFetching(undefined, action)).toEqual(false);
    });

    it('On fail fetching notes', () => {
        const action = {
            type: Actions.FAIL_FETCHING_NOTES
        };
        expect(Reducer.notesFetching(undefined, action)).toEqual(false);
    });

    it('On update notes using notesErrored', () => {
        const action = {
            type: Actions.UPDATE_NOTES
        };
        expect(Reducer.notesErrored({id: 1}, action)).toEqual({id: 1, errored: false});
    });

    it('On start fetching notes using notesErrored', () => {
        const action = {
            type: Actions.START_FETCHING_NOTES
        };
        expect(Reducer.notesErrored({id: 1}, action)).toEqual({id: 1, errored: false});
    });

    it('On fail fetching notes using notesErrored', () => {
        const action = {
            type: Actions.FAIL_FETCHING_NOTES,
            error: 'error message'
        };
        expect(Reducer.notesErrored({id: 1}, action)).toEqual({id: 1, message: 'error message', errored: true});
    });

    it('On update note using note', () => {
        const action = {
            type: Actions.UPDATE_NOTE,
            data: {title: 'message'}
        };
        expect(Reducer.note({id: 1}, action)).toEqual({id: 1, title: 'message'});
    });

    it('On create note using note', () => {
        const action = {
            type: Actions.CREATE_NOTE,
            data: {title: 'message'}
        };
        expect(Reducer.note({id: 1}, action)).toEqual({id: 1, title: 'message'});
    });

    it('On start creating note for submission using notesCreating', () => {
        const action = {
            type: Actions.START_CREATING_NOTE_FOR_SUBMISSION,
            submissionID: 1
        };
        expect(Reducer.notesCreating([2, 3], action)).toEqual([2, 3, 1]);
    });

    it('On start editing note for submission using notesCreating', () => {
        const action = {
            type: Actions.START_EDITING_NOTE_FOR_SUBMISSION,
            submissionID: 1
        };
        expect(Reducer.notesCreating([2, 3], action)).toEqual([2, 3, 1]);
    });

    it('On create note for submission using notesCreating', () => {
        const action = {
            type: Actions.CREATE_NOTE,
            submissionID: 2
        };
        expect(Reducer.notesCreating([2, 3], action)).toEqual([3]);
    });

    it('On update note for submission using notesCreating', () => {
        const action = {
            type: Actions.UPDATE_NOTE,
            submissionID: 2
        };
        expect(Reducer.notesCreating([2, 3], action)).toEqual([3]);
    });

    it('On fail creating note for submission using notesCreating', () => {
        const action = {
            type: Actions.FAIL_CREATING_NOTE_FOR_SUBMISSION,
            submissionID: 2
        };
        expect(Reducer.notesCreating([2, 3], action)).toEqual([3]);
    });

    it('On fail editing note for submission using notesCreating', () => {
        const action = {
            type: Actions.FAIL_EDITING_NOTE_FOR_SUBMISSION,
            submissionID: 2
        };
        expect(Reducer.notesCreating([2, 3], action)).toEqual([3]);
    });

    it('On update note for submission using notesCreating', () => {
        const action = {
            type: Actions.UPDATE_NOTE,
            submissionID: 2
        };
        expect(Reducer.notesFailedCreating({1: {id: 1}, 2: {id: 2}}, action)).toEqual({1: {id: 1}});
    });

    it('On create note for submission using notesCreating', () => {
        const action = {
            type: Actions.CREATE_NOTE,
            submissionID: 2
        };
        expect(Reducer.notesFailedCreating({1: {id: 1}, 2: {id: 2}}, action)).toEqual({1: {id: 1}});
    });

    it('On start creating note for submission using notesCreating', () => {
        const action = {
            type: Actions.START_CREATING_NOTE_FOR_SUBMISSION,
            submissionID: 2
        };
        expect(Reducer.notesFailedCreating({1: {id: 1}, 2: {id: 2}}, action)).toEqual({1: {id: 1}});
    });

    it('On start editing note for submission using notesCreating', () => {
        const action = {
            type: Actions.START_EDITING_NOTE_FOR_SUBMISSION,
            submissionID: 2
        };
        expect(Reducer.notesFailedCreating({1: {id: 1}, 2: {id: 2}}, action)).toEqual({1: {id: 1}});
    });

    it('On fail editing note for submission using notesCreating', () => {
        const action = {
            type: Actions.FAIL_EDITING_NOTE_FOR_SUBMISSION,
            submissionID: 2,
            error: 'error message'
        };
        expect(Reducer.notesFailedCreating({1: {id: 1}}, action)).toEqual({1: {id: 1}, 2: 'error message'});
    });

    it('On update notes for submission using notesByID', () => {
        const action = {
            type: Actions.UPDATE_NOTES,
            data: {
                results: [{id: 3}, {id: 2}]
            }
        };
        const expected = {1: {id: 1}, 3: {id: 3}, 2: {id: 2}};
        expect(Reducer.notesByID({1: {id: 1}}, action)).toEqual(expected);
    });

    it('On create note for submission using notesByID', () => {
        const action = {
            type: Actions.CREATE_NOTE,
            data: {
                id: 1,
                title: 'onr'
            }
        };
        const expected = {1: {title1: '1', id: 1, title: 'onr'}};
        expect(Reducer.notesByID({1: {title1: '1'}}, action)).toEqual(expected);
    });

    it('On update note for submission using notesByID', () => {
        const action = {
            type: Actions.UPDATE_NOTE,
            data: {
                id: 1,
                title: 'onr'
            }
        };
        const expected = {1: {title1: '1', id: 1, title: 'onr'}};
        expect(Reducer.notesByID({1: {title1: '1'}}, action)).toEqual(expected);
    });

    it('On store note for submission using editingNote', () => {
        const action = {
            type: Actions.STORE_NOTE,
            submissionID: 1,
            messageID: 2,
            message: 'message'
        };
        const expected = {2: {title1: '2'}, 1: {id: 2, message: 'message'}};
        expect(Reducer.editingNote({2: {title1: '2'}}, action)).toEqual(expected);
    });

    it('On create note for submission using editingNote', () => {
        const action = {
            type: Actions.CREATE_NOTE,
            submissionID: 2
        };
        const expected = {1: {id: 1}};
        expect(Reducer.editingNote({1: {id: 1}, 2: {id: 2}}, action)).toEqual(expected);
    });

    it('On update note for submission using editingNote', () => {
        const action = {
            type: Actions.UPDATE_NOTE,
            submissionID: 2
        };
        const expected = {1: {id: 1}};
        expect(Reducer.editingNote({1: {id: 1}, 2: {id: 2}}, action)).toEqual(expected);
    });

    it('On remove note for submission using editingNote', () => {
        const action = {
            type: Actions.REMOVE_NOTE,
            submissionID: 2
        };
        const expected = {1: {id: 1}};
        expect(Reducer.editingNote({1: {id: 1}, 2: {id: 2}}, action)).toEqual(expected);
    });
});
