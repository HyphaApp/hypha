import * as Reducer from "../statuses";
import * as Actions from "../../actions/submissions";

describe("test reducer", () => {
    it("test we get the initial data for undefined value of state", () => {
      expect(Reducer.current(undefined, {})).toBe[0];
      expect(Reducer.submissionsByStatuses(undefined, {})).toBe[0];
      expect(Reducer.statusFetchingState(undefined, {})).toEqual({isFetching: false, isError: false});
    });
})