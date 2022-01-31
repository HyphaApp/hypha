import * as actions from '../actions';
import * as ActionTypes from '../constants';
import Reducer from '../reducer';

describe('Test Device configuration Actions', () => {
    it('should return the intialize action type', () => {
        const id = 1;
        const reviewId = 2;
        const expectedResult = {
            type: ActionTypes.INITIALIZE,
            id,
            reviewId
        };
        const action = actions.initializeAction(id, reviewId);
        expect(action).toEqual(expectedResult);
    });

    it('Should return the intialize action type without passing review id', () => {
        const id = 1;
        const expectedResult = {
            type: ActionTypes.INITIALIZE,
            id,
            reviewId: null
        };
        const action = actions.initializeAction(id);
        expect(action).toEqual(expectedResult);
    });

    it('should return the review fields success action type', () => {
        const data = Reducer(undefined, {}).metaStructure;
        const expectedResult = {
            type: ActionTypes.GET_REVIEW_FIELDS_SUCCESS,
            data
        };
        const action = actions.getReviewFieldsSuccessAction(data);
        expect(action).toEqual(expectedResult);
    });
    it('should return the review values success action type', () => {
        const data = Reducer(undefined, {}).initialValues;
        const expectedResult = {
            type: ActionTypes.GET_REVIEW_VALUES_SUCCESS,
            data
        };
        const action = actions.getReviewValuesSuccessAction(data);
        expect(action).toEqual(expectedResult);
    });
    it('should return the submit review action type', () => {
        const reviewData = {is_draft: true};
        const id = 1;
        const expectedResult = {
            type: ActionTypes.SUBMIT_REVIEW_DATA,
            id,
            reviewData
        };
        const action = actions.submitReviewAction(reviewData, id);
        expect(action).toEqual(expectedResult);
    });
    it('should return the update review action type', () => {
        const reviewData = {is_draft: true};
        const id = 1;
        const reviewId = 2;
        const expectedResult = {
            type: ActionTypes.UPDATE_REVIEW_DATA,
            id,
            reviewData,
            reviewId
        };
        const action = actions.updateReviewAction(reviewData, id, reviewId);
        expect(action).toEqual(expectedResult);
    });
    it('should return the delete review action type', () => {
        const id = 1;
        const reviewId = 2;
        const expectedResult = {
            type: ActionTypes.DELETE_REVIEW_DATA,
            id,
            reviewId
        };
        const action = actions.deleteReviewAction(reviewId, id);
        expect(action).toEqual(expectedResult);
    });
    it('should return the show loading action type', () => {
        const expectedResult = {
            type: ActionTypes.SHOW_LOADING
        };
        const action = actions.showLoadingAction();
        expect(action).toEqual(expectedResult);
    });
    it('should return the hide loading action type', () => {
        const expectedResult = {
            type: ActionTypes.HIDE_LOADING
        };
        const action = actions.hideLoadingAction();
        expect(action).toEqual(expectedResult);
    });
    it('should return the clear initial values action type', () => {
        const expectedResult = {
            type: ActionTypes.CLEAR_INITIAL_VALUES
        };
        const action = actions.clearInitialValues();
        expect(action).toEqual(expectedResult);
    });
    it('should return the toggle save draft action type', () => {
        const status = Reducer(undefined, {}).saveAsDraft;
        const expectedResult = {
            type: ActionTypes.TOGGLE_SAVE_DRAFT,
            status
        };
        const action = actions.toggleSaveDraftAction(status);
        expect(action).toEqual(expectedResult);
    });
});
