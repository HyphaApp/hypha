import * as Selectors from '../messages';


describe('Test the selector of messages', () => {

    it('Get messages', () => {
        expect(Selectors.getMessages({messages: {messages: 'message'}})).toEqual('message');
    });
});
