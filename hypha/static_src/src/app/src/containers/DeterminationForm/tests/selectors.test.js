import {selectFieldsInfo, selectFieldsRenderer} from '../selectors';
import initialState from '../models';


describe('Test the selector of Determination form', () => {
    const state = {
        DeterminationFormContainer: {
            id: 1
        }
    };
    it('select fields info', () => {
        expect(selectFieldsInfo(initialState)).toEqual(initialState);
    });
    it('select selectFieldsRenderer', () => {
        expect(selectFieldsRenderer(initialState)).toEqual(initialState);
    });
    it('select selectFieldsRenderer', () => {
        expect(selectFieldsRenderer(state)).toEqual({id: 1});
    });
}
);
