import { selectScreeningInfo, selectScreeningStatuses, selectDefaultOptions, selectVisibleOptions } from '../selectors';
import initialState from "../models";


describe("Test the selector of screening decision", () => {
    it("select screening state", () => {
        expect(selectScreeningInfo(initialState)).toEqual(initialState)
    });
    it("select screening decisions", () => {
        expect(selectScreeningStatuses(initialState)).toEqual(initialState.screeningStatuses)
    });
    it("select default options", () => {
        const state = {
            ScreeningStatusContainer : {
                screeningStatuses : [
                    {id: 1, default : true, yes : true},
                    {id: 2, default : true, yes : false},
                    {id: 3, default : false, yes : true}
                ],
                loading : false
            }
        }
        expect(selectScreeningStatuses(state)).toEqual(state.ScreeningStatusContainer.screeningStatuses)
        expect(selectDefaultOptions(state)).toEqual({
            yes: {id: 1, default : true, yes : true},
            no: {id: 2, default : true, yes : false}
        })
    });
    it("select visible options", () => {
        const state = {
            ScreeningStatusContainer : {
                screeningStatuses : [
                    {id: 1, default : true, yes : true},
                    {id: 2, default : true, yes : false},
                    {id: 3, default : false, yes : true},
                    {id: 4, default : false, yes : true}
                ],
                selectedValues : [
                    {id: 1, default : true, yes : true},
                    {id: 4, default : false, yes : true}
                ],
                defaultSelectedValue: {id: 1, default : true, yes : true}
            }
        }
        expect(selectVisibleOptions(state)).toEqual([
            {id: 3, default : false, yes : true, selected: false},
            {id: 4, default : false, yes : true, selected: true}
        ])
    });
}
)
