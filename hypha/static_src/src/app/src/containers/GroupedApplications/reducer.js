import * as ActionTypes from './constants';
import initialState from './models';

const GroupedApplicationsReducer = (state = initialState, action) => {
  switch (action.type) {
    case ActionTypes.GET_APPLICATIONS_SUCCESS:
      return state.set("applications", action.data);
    case ActionTypes.SHOW_LOADING:
      return state.set("loading", true);
    case ActionTypes.HIDE_LOADING:
      return state.set("loading", false);
    // case ActionTypes.UPDATE_FILTERS_QUERY:
    //   return state.set("filterQuery", action.data)
    default:
      return state;
  }
};

export default GroupedApplicationsReducer;
