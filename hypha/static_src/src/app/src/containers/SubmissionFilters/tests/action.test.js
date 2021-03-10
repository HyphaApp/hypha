import * as actions from "../actions";
import * as ActionTypes from "../constants";
import Reducer from "../reducer";

describe("Test actions of submission filters", () => {
  it("should return the intialize action type", () => {
    const searchParams = null
    const filterAction = null
    const expectedResult = {
      type: ActionTypes.INITIALIZE,
      searchParams,
      filterAction
    };
    const action = actions.initializeAction();
    expect(action).toEqual(expectedResult);
  });
  it("should return the filter success action type", () => {
    const data = Reducer(undefined, {}).filters
    const expectedResult = {
      type: ActionTypes.GET_FILTERS_SUCCESS,
      data
    };
    const action = actions.getFiltersSuccessAction(data);
    expect(action).toEqual(expectedResult);
  });
  it("should return the update filter query action type", () => {
    const data = Reducer(undefined, {}).filterQuery
    const expectedResult = {
      type: ActionTypes.UPDATE_FILTERS_QUERY,
      data
    };
    const action = actions.updateFiltersQueryAction(data);
    expect(action).toEqual(expectedResult);
  });
  it("should return the update selected filter action type", () => {
    const filterKey = "key" 
    const value = 1
    const expectedResult = {
      type: ActionTypes.UPDATE_SELECTED_FILTER,
      value,
      filterKey
    };
    const action = actions.updateSelectedFilterAction(filterKey, value);
    expect(action).toEqual(expectedResult);
  });
  it("should return the show loading action type", () => {
    const expectedResult = {
      type: ActionTypes.SHOW_LOADING
    };
    const action = actions.showLoadingAction();
    expect(action).toEqual(expectedResult);
  });
  it("should return the hide loading action type", () => {
    const expectedResult = {
      type: ActionTypes.HIDE_LOADING
    };
    const action = actions.hideLoadingAction();
    expect(action).toEqual(expectedResult);
  });
  it("should return the delete selected filter action type", () => {
    const expectedResult = {
      type: ActionTypes.DELETE_SELECTED_FILTER
    };
    const action = actions.deleteSelectedFiltersAction();
    expect(action).toEqual(expectedResult);
  });
});