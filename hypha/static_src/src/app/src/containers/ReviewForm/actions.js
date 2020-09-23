import * as ActionTypes from './constants';

export const initializeAction = (id, reviewId = null) => ({
  type: ActionTypes.INITIALIZE,
  id,
  reviewId
});


export const getReviewFieldsSuccessAction = (data) => ({
  type: ActionTypes.GET_REVIEW_FIELDS_SUCCESS,
  data
});

export const getReviewValuesSuccessAction = (data) => ({
  type: ActionTypes.GET_REVIEW_VALUES_SUCCESS,
  data
});

export const submitReviewAction = (reviewData, id) => ({
  type: ActionTypes.SUBMIT_REVIEW_DATA,
  id,
  reviewData,
});

export const updateReviewAction = (reviewData, id, reviewId) => ({
  type: ActionTypes.UPDATE_REVIEW_DATA,
  id,
  reviewData,
  reviewId
});

export const deleteReviewAction = (reviewId, id) => ({
  type: ActionTypes.DELETE_REVIEW_DATA,
  id,
  reviewId
});

export const showLoadingAction = () => ({
	type: ActionTypes.SHOW_LOADING,
})

export const hideLoadingAction = () => ({
	type: ActionTypes.HIDE_LOADING,
})

export const clearInitialValues = () => ({
  type: ActionTypes.CLEAR_INITIAL_VALUES
})

export const toggleSaveDraftAction = (status) => ({
  type: ActionTypes.TOGGLE_SAVE_DRAFT,
  status
})