import * as ActionTypes from './constants';

export const initializeAction = (id) => ({
  type: ActionTypes.INITIALIZE,
  id
});

export const showLoadingAction = () => ({
	type: ActionTypes.SHOW_LOADING,
})

export const hideLoadingAction = () => ({
	type: ActionTypes.HIDE_LOADING,
})

export const getScreeningSuccessAction = (data) => ({
  type: ActionTypes.GET_SCREENING_STATUSES,
  data
})

export const selectDefaultValueAction = (id, data) => ({
  type: ActionTypes.SELECT_DEFAULT_VALUE,
  id,
  data
})

export const setDefaultSelectedAction = (data) => ({
  type: ActionTypes.SET_DEFAULT_VALUE,
  data
})

export const selectVisibleOptionAction = (id, data) => ({
  type: ActionTypes.SELECT_VISIBLE_OPTION,
  id,
  data
})

export const setVisibleSelectedAction = (data) => ({
  type: ActionTypes.SET_VISIBLE_OPTION,
  data
})
