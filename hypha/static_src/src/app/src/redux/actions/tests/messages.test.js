import * as actions from '../messages';
import {v4 as uuidv4} from 'uuid';


describe('Test actions', () => {

    it('Should return the dismissed message Action type', () => {
        const messageID = 1;
        const expectedResult = {
            type: actions.DISMISS_MESSAGE,
            messageID
        };
        const action = actions.dismissMessage(messageID);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the add message Action type', () => {
        const message = 'message text';
        const type = 'success';
        const action = actions.addMessage(message, type);
        expect(action.type).toEqual(actions.ADD_MESSAGE);
        expect(action.messageType).toEqual(type);
        expect(action.message).toEqual(message);
    });

    it('Should return the error msg for wrong type add message Action type', () => {
        const message = 'message text';
        const type = 'succes';
        try {
            actions.addMessage(message, type);
        }
        catch (e) {
            expect(e).toEqual('Invalid message type');
        }
    });
});
