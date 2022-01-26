import {selectGeneralInfo, selectFieldsRenderer} from '../selectors';
import initialState from '../models';


describe('Test the selector of GeneralInfo', () => {
    const state = {
        GeneralInfoContainer: {
            id: 1
        }
    };
    it('select general info', () => {
        expect(selectGeneralInfo(initialState)).toEqual(initialState);
    });
    it('select selectFieldsRenderer', () => {
        expect(selectFieldsRenderer(initialState)).toEqual(initialState);
    });
    it('select selectFieldsRenderer with GeneralInfoContainer', () => {
        expect(selectFieldsRenderer(state)).toEqual({id: 1});
    });
}
);
