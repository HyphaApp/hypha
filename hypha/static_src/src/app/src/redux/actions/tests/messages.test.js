import * as actions from '../messages';


describe("Test actions", () => {
    it("should return the dismissed message Action type", () => {
        const messageID = 1
        const expectedResult = {
          type: actions.DISMISS_MESSAGE,
          messageID,
        };
        const action = actions.dismissMessage(messageID);
        expect(action).toEqual(expectedResult);
      });
})