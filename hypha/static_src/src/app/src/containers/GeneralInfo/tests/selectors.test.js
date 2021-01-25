import { selectGeneralInfo } from '../selectors';
import initialState from "../models";


describe("Test the selector of GeneralInfo", () => {
    it("select general info", () => {
        expect(selectGeneralInfo(initialState)).toEqual(initialState)
    })
}
)