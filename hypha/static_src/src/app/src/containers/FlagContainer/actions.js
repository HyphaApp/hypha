import * as ActionTypes from './constants';

export const initAction = (flagType, title, APIPath) => ({
  type: ActionTypes.INIT,
  flagType,
  title,
  APIPath
})

export const showLoadingAction = (flagType) => ({
  type: ActionTypes.SHOW_LOADING,
  flagType
})

export const setFlagClicked = (flagType, data) => ({
  type: ActionTypes.FLAG_CLICKED,
  flagType,
  data
})

export const hideLoadingAction = (flagType) => ({
  type: ActionTypes.HIDE_LOADING,
  flagType
})

export const getSelectedFlagAction = (flagType, data) => ({
  type: ActionTypes.GET_SELECTED_FLAG,
  flagType,
  data
})

export const setFlagAction = (flagType, APIPath) => ({
  type: ActionTypes.SET_FLAG,
  flagType,
  APIPath
})
