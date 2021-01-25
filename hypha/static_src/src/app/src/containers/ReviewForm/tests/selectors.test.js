import { selectFieldsInfo } from '../selectors';
import initialState from "../models";


describe("Test the selector", () => {
    it("select initial state", () => {
        expect(selectFieldsInfo(initialState)).toEqual(initialState)
    })
}
)