import { selectFieldsInfo } from '../selectors';
import initialState from "../models";


describe("Test the selector of Determination form", () => {
    it("select fields info", () => {
        expect(selectFieldsInfo(initialState)).toEqual(initialState)
    })
}
)