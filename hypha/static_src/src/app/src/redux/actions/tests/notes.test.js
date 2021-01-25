import * as actions from '../notes';


describe("Test actions", () => {
    it("should return the removed stored note Action type", () => {
        const submissionID = 1
        const expectedResult = {
          type: actions.REMOVE_NOTE,
          submissionID
        };
        const action = actions.removedStoredNote(submissionID);
        expect(action).toEqual(expectedResult);
      });
      it("should return the writing note Action type", () => {
        const submissionID = 1
        const message = "foo"
        const expectedResult = {
          type: actions.STORE_NOTE,
          submissionID,
          message
        };
        const action = actions.writingNote(submissionID, message);
        expect(action).toEqual(expectedResult);
      });
      it("should return the editing note Action type", () => {
        const submissionID = 1
        const message = "foo"
        const messageID = 2
        const expectedResult = {
          type: actions.STORE_NOTE,
          messageID,
          submissionID,
          message
        };
        const action = actions.editingNote(messageID, message, submissionID);
        expect(action).toEqual(expectedResult);
      });
})
