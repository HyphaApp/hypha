import * as actions from "../actions";
import * as ActionTypes from "../constants";
import Reducer from "../reducer";

describe("Test actions of screening decision", () => {
  it("should return the intialize action type", () => {
    const id = 1
    const expectedResult = {
      type: ActionTypes.INITIALIZE,
      id ,
    };
    const action = actions.initializeAction(id);
    expect(action).toEqual(expectedResult);
  });
  it("should return the screening decisions success action type", () => {
    const data = Reducer(undefined, {}).screeningStatuses
    const expectedResult = {
      type: ActionTypes.GET_SCREENING_STATUSES,
      data
    };
    const action = actions.getScreeningSuccessAction(data);
    expect(action).toEqual(expectedResult);
  });
  it("should return the screening values success action type", () => {
    const data = {is_draft: true}
    const id = 1
    const expectedResult = {
      type: ActionTypes.SELECT_DEFAULT_VALUE,
      id,
      data
    };
    const action = actions.selectDefaultValueAction(id, data);
    expect(action).toEqual(expectedResult);
  });
  it("should return the select visible screening option action type", () => {
    const data = {is_draft: true}
    const id = 1
    const expectedResult = {
      type: ActionTypes.SELECT_VISIBLE_OPTION,
      id,
      data
    };
    const action = actions.selectVisibleOptionAction(id, data);
    expect(action).toEqual(expectedResult);
  });
  it("should return the set visible screening option action type", () => {
    const data= Reducer(undefined, {}).selectedValues
    const expectedResult = {
      type: ActionTypes.SET_VISIBLE_OPTION,
      data
    };
    const action = actions.setVisibleSelectedAction(data);
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
  it("should return the default selected value action type", () => {
    const data = Reducer(undefined, {}).defaultSelectedValue
    const expectedResult = {
      type: ActionTypes.SET_DEFAULT_VALUE,
      data
    };
    const action = actions.setDefaultSelectedAction(data);
    expect(action).toEqual(expectedResult);
  });
});
