import * as ActionTypes from './constants';

export const initializeAction = () => ({
  type: ActionTypes.INITIALIZE,
});

export const getFiltersSuccessAction = (data) => ({
  type: ActionTypes.GET_FILTERS_SUCCESS,
  data
});

export const deleteSelectedFiltersAction = () => ({
  type: ActionTypes.DELETE_SELECTED_FILTER
})

export const updateFiltersQueryAction = (data) => ({
  type: ActionTypes.UPDATE_FILTERS_QUERY,
  data
});

export const updateSelectedFilterAction = (filterKey, value) => ({
  type: ActionTypes.UPDATE_SELECTED_FILTER,
  filterKey, 
  value
});

export const showLoadingAction = () => ({
	type: ActionTypes.SHOW_LOADING,
})

export const hideLoadingAction = () => ({
	type: ActionTypes.HIDE_LOADING,
})
