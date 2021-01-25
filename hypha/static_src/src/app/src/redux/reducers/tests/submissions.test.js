import {
    isDeterminationDraftExist,
    currentDetermination,
    toggleDeterminationForm,
    isReviewDraftExist,
    currentReview,
    toggleReviewForm,
    currentSubmission,
    submissionsByID,
    submission,
} from "../submissions";
import * as Actions from "../../actions/submissions";

describe("test reducer", () => {
    it("test we get the initial data for undefined value of state", () => {
      expect(isDeterminationDraftExist(undefined, {})).toBe(false);
      expect(currentDetermination(undefined, {})).toBeFalsy();
      expect(toggleDeterminationForm(undefined, {})).toBe(false);
      expect(isReviewDraftExist(undefined, {})).toBe(false);
      expect(currentReview(undefined, {})).toBeFalsy();
      expect(toggleReviewForm(undefined, {})).toBe(false);
      expect(currentSubmission(undefined, {})).toBeFalsy();
      expect(submissionsByID(undefined, {})).toMatchObject({})
      expect(submission(undefined, {})).toEqual({comments: []});
    });
    it("on clear determination draft", () => {
        const action = Actions.clearDeterminationDraftAction();
        expect(isDeterminationDraftExist(undefined, action)).toBe(false);
    });
    it("on set current determination", () => {
        const determinationId = 1
        const action = Actions.setCurrentDeterminationAction(determinationId);
        expect(currentDetermination(undefined, action)).toEqual(determinationId);
    });
    it("on clear current determination", () => {
        const action = Actions.clearCurrentDeterminationAction();
        expect(currentDetermination(undefined, action)).toBeFalsy();
    });
    it("on toggle determination form", () => {
        const status = true
        const action = Actions.toggleDeterminationFormAction(status);
        expect(toggleDeterminationForm(undefined, action)).toBe(true);
    });
    it("on set current review", () => {
        const reviewId = 1
        const action = Actions.setCurrentReviewAction(reviewId);
        expect(currentReview(undefined, action)).toEqual(reviewId);
    });
    it("on clear current review", () => {
        const action = Actions.clearCurrentReviewAction();
        expect(currentReview(undefined, action)).toBeFalsy();
    });
    it("on toggle review form", () => {
        const status = true
        const action = Actions.toggleReviewFormAction(status);
        expect(toggleReviewForm(undefined, action)).toBe(true);
    });
    it("on clear current submission", () => {
        const action = Actions.clearCurrentSubmission();
        expect(currentSubmission(undefined, action)).toBeFalsy();
    });
    it("on clear all submissions", () => {
        const action = Actions.clearAllSubmissionsAction();
        expect(currentSubmission(undefined, action)).toBeFalsy();
    });
})