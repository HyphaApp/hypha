import {selectFieldsInfo, selectFieldsRenderer} from '../selectors';
import initialState from '../models';


describe('Test the selector', () => {
    it('select initial state', () => {
        expect(selectFieldsInfo(initialState)).toEqual(initialState);
    });
    const state = {
        ReviewFormContainer: {
            id: 1
        }
    };
    it('select selectFieldsRenderer', () => {
        expect(selectFieldsRenderer(initialState)).toEqual(initialState);
    });
    it('select selectFieldsRenderer', () => {
        expect(selectFieldsRenderer(state)).toEqual({id: 1});
    });
}
);
