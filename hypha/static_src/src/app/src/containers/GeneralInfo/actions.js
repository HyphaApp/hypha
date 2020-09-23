import * as ActionTypes from './constants';

export const initializeAction = () => ({
  type: ActionTypes.INITIALIZE,
  
});

export const getUserSuccessAction = (data) => ({
  type: ActionTypes.GET_USER_SUCCESS,
  data
});

export const showLoadingAction = () => ({
	type: ActionTypes.SHOW_LOADING,
})

export const hideLoadingAction = () => ({
	type: ActionTypes.HIDE_LOADING,
})
