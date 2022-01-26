import {SelectSubmissionFiltersInfo, SelectSelectedFilters} from '../selectors';
import initialState from '../models';


describe('Test the selector of submission filters', () => {
    it('select submission filters state', () => {
        expect(SelectSubmissionFiltersInfo(initialState)).toEqual(initialState);
    });
    it('get selected filters', () => {
        expect(SelectSelectedFilters(initialState)).toEqual(initialState.filterQuery);
    });
}
);
