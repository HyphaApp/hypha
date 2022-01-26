import initialState from '../models';
import Reducer from '../reducer';
import * as Actions from '../actions';

describe('test reducer of GeneralInfo', () => {
    it('test  we get the initial data for undefined value of state', () => {
        expect(Reducer(undefined, {})).toEqual(initialState);
    });
    it('on show loading', () => {
        const expected = initialState.set('loading', true);
        const action = Actions.showLoadingAction();
        expect(Reducer(initialState, action)).toEqual(expected);
    });
    it('on hide loading', () => {
        const expected = initialState.set('loading', false);
        const action = Actions.hideLoadingAction();
        expect(Reducer(initialState, action)).toEqual(expected);
    });
    it('on save as Draft', () => {
        const data = {id: 1};
        const expected = initialState.set('user', data);
        const action = Actions.getUserSuccessAction(data);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
});

