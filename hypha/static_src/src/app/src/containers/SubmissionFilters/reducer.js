import * as ActionTypes from './constants';
import initialState from './models';

const SubmissionFiltersReducer = (state = initialState, action) => {
  switch (action.type) {
    case ActionTypes.GET_FILTERS_SUCCESS:
      return state.set("filters", action.data);
    case ActionTypes.SHOW_LOADING:
      return state.set("loading", true);
    case ActionTypes.HIDE_LOADING:
      return state.set("loading", false);
    case ActionTypes.UPDATE_SELECTED_FILTER:
      if(!(action.value).length){
        let selectedFilters = {...state.selectedFilters}
        delete selectedFilters[action.filterKey]
        return state.set("selectedFilters", selectedFilters);
      }
      return state.setIn(["selectedFilters", action.filterKey], action.value);
    case ActionTypes.UPDATE_FILTERS_QUERY:
      return state.set("filterQuery", action.data)
    case ActionTypes.DELETE_SELECTED_FILTER:
      return state.set("selectedFilters", {})
    default:
      return state;
  }
};

export default SubmissionFiltersReducer;
