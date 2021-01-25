import * as actions from '../submissions';
import Reducer from "../../reducers/submissions";

describe("Test actions", () => {
    it("should return the clear Determination Draft Action type", () => {
        const expectedResult = {
          type: actions.CLEAR_DETERMINATION_DRAFT,
        };
        const action = actions.clearDeterminationDraftAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear all submissions Action type", () => {
        const expectedResult = {
          type: actions.CLEAR_ALL_SUBMISSIONS,
        };
        const action = actions.clearAllSubmissionsAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear all statuses Action type", () => {
        const expectedResult = {
          type: actions.CLEAR_ALL_STATUSES,
        };
        const action = actions.clearAllStatusesAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear all rounds Action type", () => {
        const expectedResult = {
          type: actions.CLEAR_ALL_ROUNDS,
        };
        const action = actions.clearAllRoundsAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear all current determination", () => {
        const expectedResult = {
          type: actions.CLEAR_CURRENT_DETERMINATION,
        };
        const action = actions.clearCurrentDeterminationAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear review draft", () => {
        const expectedResult = {
          type: actions.CLEAR_REVIEW_DRAFT,
        };
        const action = actions.clearReviewDraftAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear current review", () => {
        const expectedResult = {
          type: actions.CLEAR_CURRENT_REVIEW,
        };
        const action = actions.clearCurrentReviewAction();
        expect(action).toEqual(expectedResult);
      });
      it("should return the clear current submission", () => {
        const expectedResult = {
          type: actions.CLEAR_CURRENT_SUBMISSION,
        };
        const action = actions.clearCurrentSubmission();
        expect(action).toEqual(expectedResult);
      });
      it("should return toggle determination action type", () => {
        const status = true
        const expectedResult = {
          type: actions.TOGGLE_DETERMINATION_FORM,
          status
        };
        const action = actions.toggleDeterminationFormAction(status);
        expect(action).toEqual(expectedResult);
      });
      it("should return set current determination action type", () => {
        const determinationId = 1
        const expectedResult = {
          type: actions.SET_CURRENT_DETERMINATION,
          determinationId
        };
        const action = actions.setCurrentDeterminationAction(determinationId);
        expect(action).toEqual(expectedResult);
      });
      it("should return toggle review form action type", () => {
        const status = true
        const expectedResult = {
          type: actions.TOGGLE_REVIEW_FORM,
          status
        };
        const action = actions.toggleReviewFormAction(status);
        expect(action).toEqual(expectedResult);
      });
      it("should return set current review action type", () => {
        const reviewId = 1
        const expectedResult = {
          type: actions.SET_CURRENT_REVIEW,
          reviewId
        };
        const action = actions.setCurrentReviewAction(reviewId);
        expect(action).toEqual(expectedResult);
      });
      it("should return append NoteID For Submission action type", () => {
        const submissionID = 1
        const noteID = 2
        const expectedResult = {
          type: actions.ADD_NOTE_FOR_SUBMISSION,
          submissionID,
          noteID
        };
        const action = actions.appendNoteIDForSubmission(submissionID, noteID);
        expect(action).toEqual(expectedResult);
      });
      it("should return set current Submission round action type", () => {
        const submissionID = 1
        const results = []
        actions.setCurrentSubmissionRound(submissionID)(result => results.push(result));
        expect(results[0].type).toEqual(actions.SET_CURRENT_SUBMISSION_ROUND)
        expect(results.length).toEqual(5);
      });
      it("should return set current Submission action type", () => {
        const submissionID = 1
        const results = []
        actions.setCurrentSubmission(submissionID)(result => results.push(result));
        expect(results.length).toEqual(8);
        expect(results[7].type).toEqual(actions.SET_CURRENT_SUBMISSION);
      });
      it("should return set current statuses action type", () => {
        const statuses = ["status1", "status2"]
        const results = []
        actions.setCurrentStatuses(statuses)(result => results.push(result));
        expect(results[0].type).toEqual(actions.SET_CURRENT_STATUSES);
        expect(results.length).toEqual(5);
      });
      it("should return load submission from url action type", () => {
        const params = "?submission=2"
        const results = []
        const firstFunc = result => results.push(result);
        const secFunc = () => {
          return {
            submissions : {
              current : 1
            }
          }
        }
        expect(actions.loadSubmissionFromURL(params)(firstFunc, secFunc)).toBe(true);
        expect(results.length).toEqual(1);
      });
      it("should return load submission from url if url doesn't have id action type", () => {
        const params = ""
        const results = []
        const firstFunc = result => results.push(result);
        const secFunc = () => {
          return {
            submissions : {
              current : 1
            }
          }
        }
        expect(actions.loadSubmissionFromURL(params)(firstFunc, secFunc)).toBe(false);
        expect(results.length).toEqual(0);
      });
      it("should return clear current submission param action type", () => {
        const results = []
        const firstFunc = result => results.push(result);
        const secFunc = () => {
          return {
            router : {
              location : {
                search : "abc"
              }
            }
          }
        }
        actions.clearCurrentSubmissionParam()(firstFunc, secFunc)
        expect(results.length).toEqual(1);
      });
      it("should return set current submission param action type", () => {
        const results = []
        const firstFunc = result => results.push(result);
        const secFunc = () => {
          return {
            submissions : {
              current : 1
            }
          }
        }
        actions.setCurrentSubmissionParam()(firstFunc, secFunc)
        expect(results.length).toEqual(1);
      });
});
