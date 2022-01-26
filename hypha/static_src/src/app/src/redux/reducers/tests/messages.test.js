import * as Reducer from '../messages';
import * as Actions from '../../actions/messages';

describe('test reducer', () => {

    it('Test we get the initial data for undefined value of state', () => {
        expect(Reducer.messages(undefined, {})).toMatchObject({});
        expect(Reducer.message(undefined, {})).toBe(undefined);
    });

    it('On add message', () => {
        const action = {
            type: Actions.ADD_MESSAGE,
            messageID: 1,
            messageType: 'type1',
            message: 'message'
        };
        const state = {
            title: 'title1'
        };
        const expected = {
            title: 'title1',
            1: {
                id: 1,
                messageType: 'type1',
                message: 'message'
            }
        };
        expect(Reducer.messages(state, action)).toEqual(expected);
    });

    it('On dismiss message with messageID not equal with state id', () => {
        const action = {
            type: Actions.DISMISS_MESSAGE,
            messageID: 2
        };
        const state = {
            1: {
                id: 1,
                messageType: 'type1',
                message: 'message'
            }
        };
        const expected = {
            1: {
                id: 1,
                messageType: 'type1',
                message: 'message'
            }
        };
        expect(Reducer.messages(state, action)).toEqual(expected);
    });

    it('On dismiss message', () => {
        const action = {
            type: Actions.DISMISS_MESSAGE,
            messageID: 2
        };
        const state = {
            2: {
                id: 2,
                messageType: 'type1',
                message: 'message'
            }
        };
        const expected = {
            2: {
                id: 2,
                messageType: 'type1',
                message: 'message'
            }
        };
        expect(Reducer.messages(state, action)).toEqual(expected);
    });

});
