import * as actions from '../notes';
import {CALL_API} from '@middleware/api';
import api from '@api';


describe('Test actions', () => {

    it('Should return the removed stored note Action type', () => {
        const submissionID = 1;
        const expectedResult = {
            type: actions.REMOVE_NOTE,
            submissionID
        };
        const action = actions.removedStoredNote(submissionID);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the writing note Action type', () => {
        const submissionID = 1;
        const message = 'foo';
        const expectedResult = {
            type: actions.STORE_NOTE,
            submissionID,
            message
        };
        const action = actions.writingNote(submissionID, message);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the editing note Action type', () => {
        const submissionID = 1;
        const message = 'foo';
        const messageID = 2;
        const expectedResult = {
            type: actions.STORE_NOTE,
            messageID,
            submissionID,
            message
        };
        const action = actions.editingNote(messageID, message, submissionID);
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetch Notes For Submission action type', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        actions.fetchNotesForSubmission(2)(firstFunc);
        expect(results.length).toEqual(1);
        expect(results[0].submissionID).toEqual(2);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_FETCHING_NOTES, actions.UPDATE_NOTES, actions.FAIL_FETCHING_NOTES]);
    });

    it('Should return fetch Notes action type', () => {
        const submissionID = 1;
        const action = actions.fetchNotes(submissionID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_FETCHING_NOTES, actions.UPDATE_NOTES, actions.FAIL_FETCHING_NOTES],
                endpoint: api.fetchNotesForSubmission(submissionID)
            },
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return create Notes For Submission action type', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        actions.createNoteForSubmission(2, 'note')(firstFunc);
        expect(results.length).toEqual(1);
        expect(results[0].submissionID).toEqual(2);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_CREATING_NOTE_FOR_SUBMISSION, actions.CREATE_NOTE, actions.FAIL_CREATING_NOTE_FOR_SUBMISSION]);
    });

    it('Should return create Notes action type', () => {
        const submissionID = 1;
        const note = 'note';
        const action = actions.createNote(submissionID, note);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_CREATING_NOTE_FOR_SUBMISSION, actions.CREATE_NOTE, actions.FAIL_CREATING_NOTE_FOR_SUBMISSION],
                endpoint: api.createNoteForSubmission(submissionID, note)
            },
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return fetch new Notes For Submission action type', () => {
        const state = {
            submissions: {
                byID: {
                    1: {comments: [], id: 1}
                }
            }
        };
        const results = [];
        const firstFunc = result => results.push(result);
        const secondFunc = () => state;
        actions.fetchNewNotesForSubmission(1)(firstFunc, secondFunc);
        expect(results.length).toEqual(1);
        expect(results[0].submissionID).toEqual(1);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_FETCHING_NOTES, actions.UPDATE_NOTES, actions.FAIL_FETCHING_NOTES]);
    });

    it('Should return fetch new Notes For Submission action type with comment exist', () => {
        const state = {
            submissions: {
                byID: {
                    1: {comments: ['a'], id: 1}
                }
            }
        };
        const results = [];
        const firstFunc = result => results.push(result);
        const secondFunc = () => state;
        actions.fetchNewNotesForSubmission(1)(firstFunc, secondFunc);
        expect(results.length).toEqual(1);
        expect(results[0].submissionID).toEqual(1);
        expect(results[0][[CALL_API]].types).toEqual([actions.START_FETCHING_NOTES, actions.UPDATE_NOTES, actions.FAIL_FETCHING_NOTES]);
    });

    it('Should return fetch Newer Notes action type', () => {
        const submissionID = 1;
        const latestID = 'note';
        const action = actions.fetchNewerNotes(submissionID, latestID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_FETCHING_NOTES, actions.UPDATE_NOTES, actions.FAIL_FETCHING_NOTES],
                endpoint: api.fetchNewNotesForSubmission(submissionID, latestID)
            },
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });

    it('Should return editNoteForSubmission action type', () => {
        const results = [];
        const firstFunc = result => results.push(result);
        actions.editNoteForSubmission('note', 2)(firstFunc);
        expect(results.length).toEqual(1);
        expect(results[0].submissionID).toEqual(2);
        expect(results[0].note).toEqual('note');
        expect(results[0][[CALL_API]].types).toEqual([actions.START_EDITING_NOTE_FOR_SUBMISSION, actions.UPDATE_NOTE, actions.FAIL_EDITING_NOTE_FOR_SUBMISSION]);
    });

    it('Should return fetch Newer Notes action type', () => {
        const submissionID = 1;
        const note = 'note';
        const action = actions.editNote(note, submissionID);
        const expectedResult = {
            [CALL_API]: {
                types: [actions.START_EDITING_NOTE_FOR_SUBMISSION, actions.UPDATE_NOTE, actions.FAIL_EDITING_NOTE_FOR_SUBMISSION],
                endpoint: api.editNoteForSubmission(note)
            },
            note,
            submissionID
        };
        expect(action).toEqual(expectedResult);
    });
});
