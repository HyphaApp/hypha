import initialState from '../models';
import Reducer from '../reducer';
import * as Actions from '../actions';
import * as Immutable from 'seamless-immutable';


describe('test reducer of submission filters', () => {
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
    it('on getting filters success', () => {
        const data = true;
        const expected = initialState.set('filters', data);
        const action = Actions.getFiltersSuccessAction(data);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
    it('on update filter query', () => {
        const data = {is_draft: true, label: 'sample'};
        const expected = initialState.set('filterQuery', data);
        const action = Actions.updateFiltersQueryAction(data);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
    it('on delete selected filters', () => {
        const expected = initialState.set('selectedFilters', {});
        const action = Actions.deleteSelectedFiltersAction();
        expect(Reducer(undefined, action)).toEqual(expected);
    });
    it('on update selected filter', () => {
        const filterKey = 'sample-key';
        const value = [1, 2];
        const expected = initialState.setIn(['selectedFilters', filterKey], value);
        const action = Actions.updateSelectedFilterAction(filterKey, value);
        expect(Reducer(undefined, action)).toEqual(expected);
    });
    it('on update selected filter with empty value passed', () => {
        const filterKey = 'sample-key';
        const value = [];
        const initialState = Immutable.from({
            selectedFilters: {
                'sample-key': [1, 2],
                'other-key': [3, 4]
            }
        });
        const action = Actions.updateSelectedFilterAction(filterKey, value);
        expect(Reducer(initialState, action)).toEqual({
            selectedFilters: {
                'other-key': [3, 4]
            }
        });
    });
});

