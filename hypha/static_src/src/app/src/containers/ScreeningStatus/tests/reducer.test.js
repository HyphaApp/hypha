import initialState from "../models";
import Reducer from "../reducer";
import * as Actions from "../actions";

describe("test reducer of screening decision", () => {
  it("test  we get the initial data for undefined value of state", () => {
    expect(Reducer(undefined, {})).toEqual(initialState);
  });
  it("on show loading", () => {
    const expected = initialState.set("loading", true)
    const action = Actions.showLoadingAction();
    expect(Reducer(initialState, action)).toEqual(expected);
  });
  it("on hide loading", () => {
    const expected = initialState.set("loading",      false)
    const action = Actions.hideLoadingAction();
    expect(Reducer(initialState, action)).toEqual(expected);
  });
  it("on screening decisions success", () => {
    const data = { id : 1}
    const expected = initialState.set("screeningStatuses", data)
    const action = Actions.getScreeningSuccessAction(data);
    expect(Reducer(initialState, action)).toEqual(expected);
  });
  it("on default selected", () => {
    const data = {id : 1};
    const expected = initialState.set("defaultSelectedValue", data);
    const action = Actions.setDefaultSelectedAction(data);
    expect(Reducer(undefined, action)).toEqual(expected);
  });
  it("on visible selected", () => {
    const data = {is_draft : true, label : "sample"};
    const expected = initialState.set("selectedValues", data);
    const action = Actions.setVisibleSelectedAction(data);
    expect(Reducer(undefined, action)).toEqual(expected);
  });
});

