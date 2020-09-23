import * as ActionTypes from './constants';
import initialState from './models';

/* eslint-disable default-case, no-param-reassign */
const generalInfoReducer = (state = initialState, action) => {
  switch (action.type) {
    case ActionTypes.GET_USER_SUCCESS:
      return state.set("user", action.data);
    case ActionTypes.SHOW_LOADING:
      return state.set("loading", true);
    case ActionTypes.HIDE_LOADING:
      return state.set("loading", false);
    default:
      return state;
  }
};

export default generalInfoReducer;