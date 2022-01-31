import initialState from '../models';
import Reducer from '../reducer';
import * as Actions from '../actions';

describe('test reducer of determination form', () => {
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
    it('on clear initial values', () => {
        const expected = initialState.set('initialValues', null);
        const action = Actions.clearInitialValues();
        expect(Reducer(initialState, action)).toEqual(expected);
    });
    it('on save as Draft', () => {
        const data = true;
        const expected = initialState.set('saveAsDraft', data);
        const action = Actions.toggleSaveDraftAction(data);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
    it('on determination values success', () => {
        const data = {is_draft: true, label: 'sample'};
        const expected = initialState.set('initialValues', data);
        const action = Actions.getDeterminationValuesSuccessAction(data);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
    it('on determination fields success', () => {
        const data = {is_draft: true, label: 'sample'};
        const expected = initialState.set('metaStructure', data).set('initialValues', null);
        const action = Actions.getDeterminationFieldsSuccessAction(data);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
});

