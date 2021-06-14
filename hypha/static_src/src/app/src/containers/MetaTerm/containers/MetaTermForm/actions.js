import * as ActionTypes from './constants';

export const initializeAction = () => ({
  type: ActionTypes.INITIALIZE,
});

export const getMetaTermsSuccessAction = (data) => ({
  type: ActionTypes.GET_META_TERMS_SUCCESS,
  data
});

export const showLoadingAction = () => ({
	type: ActionTypes.SHOW_LOADING,
})

export const hideLoadingAction = () => ({
	type: ActionTypes.HIDE_LOADING,
})

export const updateMetaTermsAction = (data, submissionId) => ({
  type: ActionTypes.UPDATE_META_TERMS,
  submissionId,
  data,
});

export const setSelectedMetaTermsAction = (data) => ({
  type: ActionTypes.SET_SELECTED_META_TERMS,
  data
});
