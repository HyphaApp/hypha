import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const flagContainerReducer = (state = initialState, action) => {
  switch (action.type) {
    case ActionTypes.INIT:
      return state.set(action.flagType, {
        "title" : action.title,
        "APIPath": action.APIPath,
        "loading" : true,
        "isFlagged": false,
        "isFlagClicked":  false
    })
    case ActionTypes.FLAG_CLICKED:
      return state.setIn([action.flagType, "isFlagClicked"], action.data)
    case ActionTypes.SHOW_LOADING:
      return state.setIn([action.flagType, "loading"], true);
    case ActionTypes.HIDE_LOADING:
      return state.setIn([action.flagType, "loading"], false);
    case ActionTypes.GET_SELECTED_FLAG:
      return state.setIn([action.flagType, "isFlagged"], action.data).setIn([action.flagType, "loading"], false);
    case ActionTypes.SET_FLAG:
      return state.setIn([action.flagType, "isFlagged"], !state[action.flagType].isFlagged)
    default:
      return state;
  }
};

export default flagContainerReducer;
